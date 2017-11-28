# Total Returns
# 3.12
 
# Alpha
# 0.12
 
# Beta
# 0.79
# Sharpe
# 0.93
 
# Sortino
# 1.27
 
# Max Drawdown
# 0.54
# Benchmark Returns
# 1.85
 
# Volatility
# 0.24
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline import CustomFactor
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.data import morningstar
import numpy as np
from collections import defaultdict

class MomentumRatio(CustomFactor):
   
    inputs = [USEquityPricing.close]
    window_length = 10

    # Divide the current price by the starting price to get momentum ratio
    def compute(self, today, assets, out, input1):
     out[:] = input1[-1]/input1[0]

class market_cap(CustomFactor):
   inputs = [USEquityPricing.close, morningstar.valuation.shares_outstanding]
   window_length = 1

   def compute(self, today, assets, out, close, shares):
     out[:] = close[-1] * shares[-1]

class efficiency_ratio(CustomFactor):
   inputs = [USEquityPricing.close, USEquityPricing.high, USEquityPricing.low]
   window_length = 252

   def compute(self, today, assets, out, close, high, low):
       lb = self.window_length
       e_r = np.zeros(len(assets), dtype=np.float64)
       a=np.array(([high[1:(lb):1]-low[1:(lb):1],abs(high[1:(lb):1]-close[0:(lb-1):1]),abs(low[1:(lb):1]-close[0:(lb-1):1])]))
       b=a.T.max(axis=1)
       c=b.sum(axis=1)
       e_r=abs(close[-1]-close[0]) /c
       out[:] = e_r

def initialize(context):
    set_nodata_policy(NoDataPolicy.LOG_ONLY)
    set_commission(commission.PerShare(cost=0.005, min_trade_cost=1.00))
    schedule_function(rebalance, date_rules.month_start(days_offset=5), time_rules.market_open(minutes=30))
    # half_days is True by default
    schedule_function(close_orders, date_rules.week_end(), time_rules.market_close(minutes=30))
    schedule_function(daily_run,date_rules.every_day(),time_rules.market_open(minutes=30))
    set_do_not_order_list(security_lists.leveraged_etf_list)
    context.acc_leverage  = 1.00
    context.holdings      = 10 #system rotates into the top "X" stocks each month
    context.profit_taking_factor = 0.99 #% of your total holding in a stock for which you take profit
    context.profit_target = defaultdict(lambda:100000) # this dictionary holds the profit target for each stock
    context.profit_taking_multiple  = 2 #set at 2, profit is taken when the stock doubles
    context.efficiency_limit = 0.31
    context.stop_pct      = 0.75 #the stock will be exited when it declines to this percentage of its entry price
    context.stop_price    = defaultdict(lambda:0) # this dictionary holds the trailing stop price for each stock

    pipe = Pipeline()
    attach_pipeline(pipe, 'ranked_stocks')

    factor1 = MomentumRatio(inputs=[USEquityPricing.close], window_length=20)
    pipe.add(factor1, 'factor_1')
    factor2 = MomentumRatio(inputs=[USEquityPricing.close], window_length=60)
    pipe.add(factor2, 'factor_2')
    factor3 = MomentumRatio(inputs=[USEquityPricing.close], window_length=125)
    pipe.add(factor3, 'factor_3')
    factor4 = MomentumRatio(inputs=[USEquityPricing.close], window_length=252)
    pipe.add(factor4, 'factor_4')
    factor5=efficiency_ratio()
    pipe.add(factor5, 'factor_5')

    mkt_screen = market_cap()
    stocks = mkt_screen.top(500)
    factor_5_filter = factor5 > context.efficiency_limit
    total_filter = (stocks& factor_5_filter)
    pipe.set_screen(total_filter)

    factor1_rank = factor1.rank(mask=total_filter, ascending=False)
    pipe.add(factor1_rank, 'f1_rank')
    factor2_rank = factor2.rank(mask=total_filter, ascending=False)
    pipe.add(factor2_rank, 'f2_rank')
    factor3_rank = factor3.rank(mask=total_filter, ascending=False)
    pipe.add(factor3_rank, 'f3_rank')
    factor4_rank = factor4.rank(mask=total_filter, ascending=False)
    pipe.add(factor4_rank, 'f4_rank')

    combo_raw = (factor1_rank+factor2_rank+factor3_rank+factor4_rank) / 4
    pipe.add(combo_raw, 'combo_raw')
    pipe.add(combo_raw.rank(mask=total_filter), 'combo_rank')

    # for pvr()
    c = context
    c.max_lvrg = 0
    c.risk_hi  = 0
    c.date_prv = ''
    c.cash_low = c.portfolio.starting_cash
    c.date_end = str(get_environment('end').date())
    log.info('{} to {}  {}  {}'.format(str(get_datetime().date()), c.date_end,
        int(c.cash_low), get_environment('data_frequency')))

def before_trading_start(context, data):
    context.output = pipeline_output('ranked_stocks')

    ranked_stocks = context.output.fillna(0)
    context.stock_list = ranked_stocks.sort(['combo_rank'], ascending=True).iloc[:context.holdings]

    update_universe(context.stock_list.index)

def handle_data(context, data):
    pvr(context, data)
    track_orders(context, data)
        
def daily_run(context, data):
    
    open_orders = get_open_orders()
    print "Long List"
    log.info("\n" + str(context.stock_list.sort(['combo_rank'], ascending=True).head(context.holdings)))
    
    for stock in context.portfolio.positions:
        position = context.portfolio.positions[stock]
        # Check to make sure that the position isn't flat and that there aren't pending orders
        if position.amount == 0 or stock in open_orders:
            continue   # Skip to the next stock
        
        if stock in data and 'price' in data[stock]:
           #set stop price
           price = data[stock].price  
           context.stop_price[stock] = max(context.stop_price[stock], context.stop_pct * price) 
            
           if price < context.stop_price[stock]:
              #exit when trailing stop hit
              o = order_target(stock, 0)
              oo = get_order(o)
              context.stop_price[stock] = 0
              message = 'Stoploss closing {0.amount} / {1.amount} shares of {0.sid.symbol}'.format(oo, position)
              log.info(message)
            
           if (stock.end_date - get_datetime()).days <= 2:   
              #exit soon to be delisted stocks
              o = order_target_percent(stock, 0.0)
              oo = get_order(o)
              message = 'Closing {0.amount} / {1.amount} shares of delisted symbol {0.sid.symbol}'.format(oo, position)
              log.info(message)
                
           if context.profit_target[stock] is not None and price > context.profit_target[stock]:               
              context.profit_target[stock] = price*context.profit_taking_multiple
              profit_taking_amount = int(context.portfolio.positions[stock].amount * (1 - context.profit_taking_factor))
              o = order_target(stock, profit_taking_amount)
              oo = get_order(o)
              if oo is None:
                  message = 'Take profit failed for {0} shares of {1}'.format(profit_taking_amount, stock.symbol)
              else:
                  message = 'Taking profit on {0.amount} / {1.amount} shares of {0.sid.symbol}'.format(oo, position)
              log.info(message)
#context.profit_target[stock]
def rebalance(context,data):
    
   weight = context.acc_leverage / len(context.stock_list)
   open_orders = get_open_orders()
    
   for stock in context.stock_list.index:
     if stock in open_orders:
            continue
     # buy stocks newly come into the top "X"
     if ((stock in data) and 'price' in data[stock]
        and (context.portfolio.positions[stock].amount==0)        
        and (context.stock_list.factor_1[stock] > 1)
        and (stock not in security_lists.leveraged_etf_list)):              
             o = order_target_percent(stock, weight)
             oo = get_order(o)
             if oo is None:
                message = 'Open order failed for {0.symbol}, price {1}'.format(stock, data[stock].price)
             else:
                message = 'Adding position for {0.amount} shares of {0.sid.symbol}'.format(oo)
             log.info(message)
             #set initial profit target
             context.profit_target[stock] = data[stock].price * context.profit_taking_multiple

   for stock in context.portfolio.positions.iterkeys():
        #exit postions no longer in top "X" or where the short term momentum is flat or negative
        
        position = context.portfolio.positions[stock]
        
        if ((stock not in context.stock_list.index or context.stock_list.factor_1[stock] <= 1)
           and (stock in data) and 'price' in data[stock] 
           and (stock not in open_orders)
           and ('price' in data[stock])
           and position.amount > 0): # Added check to not send close orders for empty positions
           o = order_target(stock, 0)
           oo = get_order(o)
           message = 'Exiting {0.amount} / {1.amount} shares of {0.sid.symbol}'.format(oo, position)
           log.info(message)
        #cut back winning positions to equal weighting but do not increase losing positions to equal weighting
        elif ((position.amount* position.last_sale_price
           >weight*context.portfolio.portfolio_value) 
           and (stock in data) and 'price' in data[stock] 
           and (stock not in open_orders)
           and ('price' in data[stock])):
           o = order_target_percent(stock, weight)
           oo = get_order(o)
           if oo is not None:
               message = 'Rebalancing  {0.amount} / {1.amount} shares of {0.sid.symbol}'.format(oo, position)
               log.info(message)
           else:
               message = 'Rebalancing skipped for {0.sid.symbol}'.format(position)
               log.info(message)
           

def close_orders(context, data):
    orders = get_open_orders()
    if orders:
     for o in orders:
       cancel_order(o)

def pvr(context, data):
    ''' Custom chart and/or log of profit_vs_risk returns and related information
    '''
    # # # # # # # # # #  Options  # # # # # # # # # #
    record_max_lvrg = 1          # Maximum leverage encountered
    record_leverage = 0          # Leverage (context.account.leverage)
    record_q_return = 0          # Quantopian returns (percentage)
    record_pvr      = 1          # Profit vs Risk returns (percentage)
    record_pnl      = 0          # Profit-n-Loss
    record_shorting = 1          # Total value of any shorts
    record_risk     = 0          # Risked, maximum cash spent or shorts in excess of cash at any time
    record_risk_hi  = 1          # Highest risk overall
    record_cash     = 0          # Cash available
    record_cash_low = 1          # Any new lowest cash level
    logging         = 1          # Also log to the logging window conditionally (1) or not (0)
    log_method      = 'risk_hi'  # 'daily' or 'risk_hi'

    c = context                          # For brevity
    new_cash_low = 0                     # To trigger logging in cash_low case
    date = str(get_datetime().date())    # To trigger logging in daily case
    cash = c.portfolio.cash

    if int(cash) < c.cash_low:    # New cash low
        new_cash_low = 1
        c.cash_low   = int(cash)
        if record_cash_low:
            record(CashLow = int(c.cash_low))

    pvr_rtrn      = 0        # Profit vs Risk returns based on maximum spent
    profit_loss   = 0        # Profit-n-loss
    shorts        = 0        # Shorts value
    start         = c.portfolio.starting_cash
    cash_dip      = int(max(0, start - cash))

    if record_cash:
        record(Cash = int(c.portfolio.cash))  # Cash

    if record_leverage:
        record(Lvrg = c.account.leverage)     # Leverage

    if record_max_lvrg:
        if c.account.leverage > c.max_lvrg:
            c.max_lvrg = c.account.leverage
            record(MaxLv = c.max_lvrg)        # Maximum leverage

    if record_pnl:
        profit_loss = c.portfolio.pnl
        record(PnL = profit_loss)             # "Profit and Loss" in dollars

    for p in c.portfolio.positions:
        shrs = c.portfolio.positions[p].amount
        if shrs < 0:
            shorts += int(abs(shrs * data[p].price))

    if record_shorting:
        record(Shorts = shorts)               # Shorts value as a positve

    risk = int(max(cash_dip, shorts))
    if record_risk:
        record(Risk = risk)                   # Amount in play, maximum of shorts or cash used

    new_risk_hi = 0
    if risk > c.risk_hi:
        c.risk_hi = risk
        new_risk_hi = 1

        if record_risk_hi:
            record(RiskHi = c.risk_hi)       # Highest risk overall

    if record_pvr:      # Profit_vs_Risk returns based on max amount actually spent (risk high)
        if c.risk_hi != 0:     # Avoid zero-divide
            pvr_rtrn = 100 * (c.portfolio.portfolio_value - start) / c.risk_hi
            record(PvR = pvr_rtrn)            # Profit_vs_Risk returns

    q_rtrn = 100 * (c.portfolio.portfolio_value - start) / start
    if record_q_return:
        record(QRet = q_rtrn)                 # Quantopian returns to compare to pvr returns curve

    from pytz import timezone
    if logging:
        if log_method == 'risk_hi' and new_risk_hi \
          or log_method == 'daily' and c.date_prv != date \
          or c.date_end == date \
          or new_cash_low:
            qret   = 'QRet '    + '%.1f' % q_rtrn
            mxlv   = 'MaxLv '   + '%.1f' % c.max_lvrg   if record_max_lvrg else ''
            pvr    = 'PvR '     + '%.1f' % pvr_rtrn     if record_pvr      else ''
            pnl    = 'PnL '     + '%.0f' % profit_loss  if record_pnl      else ''
            csh    = 'Cash '    + '%.0f' % cash         if record_cash     else ''
            csh_lw = 'CshLw '   + '%.0f' % c.cash_low   if record_cash_low else ''
            shrt   = 'Shrt '    + '%.0f' % shorts       if record_shorting else ''
            risk   = 'Risk '    + '%.0f' % risk         if record_risk     else ''
            rsk_hi = 'RskHi '   + '%.0f' % c.risk_hi    if record_risk_hi  else ''
            minute = get_datetime().astimezone(timezone('US/Eastern')).time().minute
            log.info('{} {} {} {} {} {} {} {} {} {}'.format(
                    minute, mxlv, qret, pvr, pnl, csh, csh_lw, shrt, risk, rsk_hi))

    if c.date_end == date:    # Log on last day, like cash 125199  portfolio 126890
        log.info('cash {}  portfolio {}'.format(
                int(cash), int(c.portfolio.portfolio_value)))

    c.date_prv = date

# https://www.quantopian.com/posts/track-orders
def track_orders(context, data):  # Log orders created or filled.
    if 'orders' not in context:
        context.orders = {}

    to_delete = []
    for id in context.orders:
        o   = get_order(id)
        sec = o.sid
        sym = sec.symbol
        if o.filled:        # Filled at least some, status 1 is Filled
            trade = 'Bot' if o.amount > 0 else 'Sold'
            log.info('      {} {} {} at {}\n'.format(
                    trade, o.filled, sym, data[sec].price))
            to_delete.append(o.id)
        else:
            log.info('         {} {} unfilled\n'.format(o.sid.symbol, o.amount))

    for sec, oo_for_sid in get_open_orders().iteritems(): # Open orders
        sym = sec.symbol
        for o in oo_for_sid: # Orders per security
            if o.id in to_delete:
                continue
            if o.status == 2:                 # Cancelled
                log.info('    Cancelled {} {} order\n'.format(
                        trade, o.amount, sym, data[sec].price))
                to_delete.append(o.id)
            elif o.id not in context.orders:  # New
                context.orders[o.id] = 1
                trade = 'Buy' if o.amount > 0 else 'Sell'
                if o.limit:        # Limit order
                    log.info('   {} {} {} now {} limit {}\n'.format(
                            trade, o.amount, sym, data[sec].price, o.limit))
                elif o.stop:       # Stop order
                    log.info('   {} {} {} now {} stop {}\n'.format(
                            trade, o.amount, sym, data[sec].price, o.stop))
                else:              # Market order
                    log.info('   {} {} {} at {}\n'.format(
                            trade, o.amount, sym, data[sec].price))
    for d in to_delete:
        del context.orders[d]




