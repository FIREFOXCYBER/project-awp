# Total Returns
# 13.30
 
# Alpha
# 0.90
 
# Beta
# 0.85
# Sharpe
# 3.20
 
# Sortino
# 4.35
 
# Max Drawdown
# 0.52
# Benchmark Returns
# 1.92
 
# Volatility
# 0.32

from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline import CustomFactor
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.data import morningstar
import numpy as np
from collections import defaultdict

class momentum_factor_1(CustomFactor):
   inputs = [USEquityPricing.close]
   window_length = 20

   def compute(self, today, assets, out, close):
     out[:] = close[-1]/close[0]

class momentum_factor_2(CustomFactor):
   inputs = [USEquityPricing.close]
   window_length = 60

   def compute(self, today, assets, out, close):
     out[:] = close[-1]/close[0]

class momentum_factor_3(CustomFactor):
   inputs = [USEquityPricing.close]
   window_length = 125

   def compute(self, today, assets, out, close):
     out[:] = close[-1]/close[0]

class momentum_factor_4(CustomFactor):
   inputs = [USEquityPricing.close]
   window_length = 252

   def compute(self, today, assets, out, close):
     out[:] = close[-1]/close[0]

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
    set_commission(commission.PerShare(cost=0.005, min_trade_cost=1.00))
    schedule_function(rebalance, date_rules.month_start(days_offset=5), time_rules.market_open())
    # half_days is True by default
    schedule_function(close_orders, date_rules.week_end(), time_rules.market_close())

    set_do_not_order_list(security_lists.leveraged_etf_list)
    context.acc_leverage  = 1.00
    context.holdings      = 10
    context.profit_taking_factor = 0.01
    context.profit_target = {}
    context.profit_taken  = {}
    context.entry_date    = {}
    context.stop_pct      = 0.75
    context.stop_price    = defaultdict(lambda:0)

    pipe = Pipeline()
    attach_pipeline(pipe, 'ranked_stocks')

    factor1 = momentum_factor_1()
    pipe.add(factor1, 'factor_1')
    factor2 = momentum_factor_2()
    pipe.add(factor2, 'factor_2')
    factor3 = momentum_factor_3()
    pipe.add(factor3, 'factor_3')
    factor4 = momentum_factor_4()
    pipe.add(factor4, 'factor_4')
    factor5=efficiency_ratio()
    pipe.add(factor5, 'factor_5')

    mkt_screen = market_cap()
    stocks = mkt_screen.top(3000)
    factor_5_filter = factor5 > 0.031
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
    ranked_stocks = context.output[context.output.factor_1 > 0]
    ranked_stocks = context.output[context.output.factor_2 > 0]
    ranked_stocks = context.output[context.output.factor_3 > 0]
    ranked_stocks = context.output[context.output.factor_4 > 0]
    ranked_stocks = context.output[context.output.factor_5 > 0]

    context.stock_list = ranked_stocks.sort(['combo_rank'], ascending=True).iloc[:context.holdings]

    update_universe(context.stock_list.index)

def handle_data(context, data):
    for stock in context.portfolio.positions:
           price = data[stock].price
           context.stop_price[stock] = max(context.stop_price[stock], context.stop_pct * price)
    for stock in context.portfolio.positions:
       if data[stock].price < context.stop_price[stock]:
           order_target(stock, 0)
           context.stop_price[stock] = 0

    current_date = get_datetime()

    # garyha turned this off to make room for some pvr options, turn some of those off to turn these on.
    #record(leverage=context.account.leverage, positions=len(context.portfolio.positions))

    for stock in context.portfolio.positions:
       if (stock.end_date - current_date).days < 2:
        order_target_percent(stock, 0.0)
        print "Long List"
        log.info("\n" + str(context.stock_list.sort(['combo_rank'], ascending=True).head(context.holdings)))

       if data[stock].close_price > context.profit_target[stock]:
        context.profit_target[stock] = data[stock].close_price*1.25
        profit_taking_amount = context.portfolio.positions[stock].amount * context.profit_taking_factor
        order_target(stock, profit_taking_amount)

    pvr(context, data)

    # garyha took the liberty of adding this, comment to turn this off
    track_orders(context, data)

def rebalance(context,data):
   weight = context.acc_leverage / len(context.stock_list)
   for stock in context.stock_list.index:
     if stock in data:
      if context.stock_list.factor_1[stock] > 1:
        if (stock.end_date - get_datetime()).days > 35:
            if stock not in security_lists.leveraged_etf_list:
              # Consider ...
              #if get_open_orders(stock): continue
              order_target_percent(stock, weight)
              context.profit_target[stock] = data[stock].close_price * 1.25

   for stock in context.portfolio.positions.iterkeys():
     if stock not in context.stock_list.index or context.stock_list.factor_1[stock] <= 1:
       order_target(stock, 0)

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

