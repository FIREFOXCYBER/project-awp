"""
    Version 1
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters import Q1500US 
from quantopian.pipeline.factors import CustomFactor

import pandas as pd
import numpy as np
from scipy import stats

# Calculate Beta
def _beta(ts, benchmark, benchmark_var):
    return np.cov(ts, benchmark)[0, 1] / benchmark_var 


class Beta(CustomFactor):
    # 60 days close price    
    inputs = [USEquityPricing.close]
    window_length = 60
    
    def compute(self, today, assets, out, close):
        # Return of Asset
        returns = pd.DataFrame(close, columns=assets).pct_change()[1:]
        # Return of Benchmark SPY500
        spy_returns = returns[sid(8554)]
        # Variance of Benchmark
        spy_returns_var = np.var(spy_returns)
        # Calculate Beta
        out[:] = returns.apply(_beta, args=(spy_returns,spy_returns_var,))
        
# Dollar value total
class AvgDailyDollarVolumeTraded(CustomFactor):
    
    inputs = [USEquityPricing.close, USEquityPricing.volume]
    window_length = 20
    
    def compute(self, today, assets, out, close_price, volume):
        out[:] = np.mean(close_price * volume, axis=0)
        
        
def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')

    context.shorts = None
    context.longs = None

    set_commission(commission.PerShare(cost=0.005, min_trade_cost=1))
    set_slippage(slippage.FixedSlippage(spread=0))
    set_benchmark(sid(8554))
    
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.month_start())

    schedule_function(remove_to_be_delisted, date_rules.every_day(), time_rules.market_open())
    schedule_function(cancel_open_orders, date_rules.every_day(), time_rules.market_close()) 

    # Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())
     

         
def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    
    # Base universe set to the Q1500US
    # base_universe = Q1500US()

    # Factor of yesterday's close price.
    # yesterday_close = USEquityPricing.close.latest
     
    pipe = Pipeline()
    pipe = attach_pipeline(pipe, name='beta_metrics')
    pipe.add(Beta(), "beta")
    
    dollar_volume = AvgDailyDollarVolumeTraded()
    
    # Screen out penny stocks and low liquidity securities.
    pipe.set_screen(dollar_volume > 10**7)

    return pipe
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    # context.output = pipeline_output('my_pipeline')
  
    # These are the securities that we are interested in trading each day.
    # context.security_list = context.output.index

    results = pipeline_output('beta_metrics').dropna()         
    ranks = results["beta"].abs().rank().order()
    
    context.shorts = ranks.tail(50)
    context.longs = ranks.head(50)
    print "Long:"
    print results.loc[context.longs.head().index]
    print "Short:"
    print results.loc[context.shorts.head().index]
    
    # The pipe character "|" is the pandas union operator
    update_universe(context.longs.index | context.shorts.index)
     
def my_assign_weights(context, data):
    """
    Assign weights to securities that we want to order.
    """
    pass
 
def my_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    print "Called monthly rebalance"
    for security in context.shorts.index:
        if get_open_orders(security):
            continue
        if security in data:
            order_target_percent(security, -0.49 / len(context.shorts))
            
    for security in context.longs.index:
        if get_open_orders(security):
            continue
        if security in data:
            order_target_percent(security, 0.49 / len(context.longs))
            
    for security in context.portfolio.positions:
        if get_open_orders(security):
            continue
        if security in data:
            if security not in (context.longs.index | context.shorts.index):
                order_target_percent(security, 0)
 
def my_record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    record(lever=context.account.leverage,
           exposure=context.account.net_leverage,
           num_pos=len(context.portfolio.positions),
           open_order=len(get_open_orders()))
 
def handle_data(context,data):
    """
    Called every minute.
    """
    
def cancel_open_orders(context, data):
    print "Called Daily rebalance 1"
    for security in get_open_orders():
        for order in get_open_orders(security):
            cancel_order(order)
            
def remove_to_be_delisted(context, data):
    print "Called Daily rebalance 2"
    for security in context.portfolio.positions:        
        if (security.end_date - get_datetime()).days < 5: 
            order_target_percent(security, 0)
