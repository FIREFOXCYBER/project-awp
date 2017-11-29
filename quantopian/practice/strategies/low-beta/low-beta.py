from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
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
        # Return of Benchmark
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

# Put any initialization logic here.  The context object will be passed to
# the other methods in your algorithm.
def initialize(context):
    
    pipe = Pipeline()
    pipe = attach_pipeline(pipe, name='beta_metrics')
    pipe.add(Beta(), "beta")
    
    dollar_volume = AvgDailyDollarVolumeTraded()
    
    # Screen out penny stocks and low liquidity securities.
    pipe.set_screen(dollar_volume > 10**7)
    context.shorts = None
    context.longs = None
    
    schedule_function(remove_to_be_delisted, date_rules.every_day(), time_rules.market_open())
    schedule_function(rebalance, date_rules.month_start())
    schedule_function(cancel_open_orders, date_rules.every_day(), time_rules.market_close())
    set_commission(commission.PerShare(cost=0.005, min_trade_cost=1))
    set_slippage(slippage.FixedSlippage(spread=0))
    set_benchmark(sid(41891))

    # record(lever=context.account.leverage,
    #        exposure=context.account.net_leverage,
    #        num_pos=len(context.portfolio.positions),
    #        open_order=len(get_open_orders()))
    
def before_trading_start(context, data):
    results = pipeline_output('beta_metrics').dropna()         
    ranks = results["beta"].abs().rank().order()
    
    context.shorts = ranks.tail(20)
    context.longs = ranks.head(20)
    
    print results.loc[context.longs.head().index]
    print results.loc[context.shorts.head().index]
    
    # The pipe character "|" is the pandas union operator
    update_universe(context.longs.index | context.shorts.index)
    

# Will be called on every trade event for the securities you specify. Every Minute 
def handle_data(context, data):
    record(lever=context.account.leverage,
           exposure=context.account.net_leverage,
           num_pos=len(context.portfolio.positions),
           open_order=len(get_open_orders()))

    
def cancel_open_orders(context, data):
    for security in get_open_orders():
        for order in get_open_orders(security):
            cancel_order(order)
            
def remove_to_be_delisted(context, data):
    for security in context.portfolio.positions:        
        if (security.end_date - get_datetime()).days < 5: 
            order_target_percent(security, 0)
        
    
def rebalance(context, data):
    for security in context.shorts.index:
        if get_open_orders(security):
            continue
        if security in data:
            order_target_percent(security, -0.5 / len(context.shorts))
            
    for security in context.longs.index:
        if get_open_orders(security):
            continue
        if security in data:
            order_target_percent(security, 0.5 / len(context.longs))
            
    for security in context.portfolio.positions:
        if get_open_orders(security):
            continue
        if security in data:
            if security not in (context.longs.index | context.shorts.index):
                order_target_percent(security, 0)
