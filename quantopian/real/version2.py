"""
    Version 2
"""
# Quantopian Dependencies
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.factors import RollingLinearRegressionOfReturns
from quantopian.pipeline.factors import AnnualizedVolatility
from quantopian.pipeline.factors import SimpleMovingAverage
from quantopian.pipeline.filters import Q1500US 
from quantopian.pipeline.factors import CustomFactor
from quantopian.pipeline.data import morningstar 
import talib as ta
# Python dependencies
import pandas as pd
import numpy as np
from scipy import stats



# Calculate Beta
def _beta(asset_return, benchmark, benchmark_var):

    return np.cov(asset_return, benchmark)[0, 1] / benchmark_var 

class Beta(CustomFactor):

    # Default parameters
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
        out[:] = returns.apply(_beta, args=(spy_returns, spy_returns_var,))
        

# AverageDollarValue()
# from quantopian.pipeline.factors import AverageDollarVolume
# Average Traded Value based on previous 20 days
class AvgDailyDollarVolumeTraded(CustomFactor):
    
    inputs = [USEquityPricing.close, USEquityPricing.volume]
    window_length = 20
    
    def compute(self, today, assets, out, close, volume):
        out[:] = np.mean(close * volume, axis=0)
  


# Momentum for 5 days
class momentum_5(CustomFactor):    

  # Set default values
  inputs = [USEquityPricing.close]   
  window_length = 5
   
  def compute(self, today, assets, out, close):  
   out[:] = close[-1]/close[0]



# Momentum for 20 days
class momentum_20(CustomFactor):    

  # Set default values
  inputs = [USEquityPricing.close]   
  window_length = 20  
   
  def compute(self, today, assets, out, close):  
   out[:] = close[-1]/close[0]
   


# Momentum for 60 days
class momentum_60(CustomFactor):    

  inputs = [USEquityPricing.close]   
  window_length = 60  
   
  def compute(self, today, assets, out, close):
   out[:] = close[-1]/close[0]
   


# Momentum for 125 days
class momentum_125(CustomFactor):    

  inputs = [USEquityPricing.close]   
  window_length = 125  
   
  def compute(self, today, assets, out, close):
   out[:] = close[-1]/close[0]
   


# Momentum for 252 days
class momentum_252(CustomFactor):    

   inputs = [USEquityPricing.close]   
   window_length = 252  
     
   def compute(self, today, assets, out, close):
     out[:] = close[-1]/close[0]
   


# from quantopian.pipeline.data import morningstar as mstar
# mstar.valuation.market_cap.latest
# lastest market_cap   
class market_cap(CustomFactor):    

   inputs = [USEquityPricing.close, morningstar.valuation.shares_outstanding]   
   # inputs = [morningstar.valuation.market_cap.latest]
   window_length = 1  
     
   def compute(self, today, assets, out, close, shares):      #close, 
     out[:] = close[-1] * shares[-1]        
     # out[:] =  market_cap[0]       
        




"""##########################################################################################

  1. Above are factor classes
  2. Below are strategy major components

##########################################################################################"""
 

         
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

    # Add other filters
    factor1 = AverageDollarVolume(window_length=20)
    pipe.add(factor1, 'Avg_dollar_Volume')
    market_cap1 = market_cap()
    pipe.add(market_cap1, 'market_cap1')
    mom5 = momentum_5()
    pipe.add(mom5, 'mom_5')
    annual_vol = AnnualizedVolatility()
    pipe.add(annual_vol, 'annual_vol')
    sma3 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=3)
    pipe.add(sma3, 'sma3')
    sma5 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=5)
    pipe.add(sma5, 'sma5')
    sma20 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=20)
    pipe.add(sma20, 'sma20')
    
    # Set pipeline screen
    factor1_filter = factor1 > 10**7
    market_cap_top = market_cap1 < 10*10**9
    market_cap_bottom = market_cap1 > 2*10**9
    # annual_vol_filter = annual_vol < 0.2
    # sma_filter = (sma3 > sma5) & (sma5 > sma20)
    # mom5_filter = mom5 > 1

    total_filter = (factor1_filter & market_cap_bottom & market_cap_top)# & annual_vol_filter) #and mom5_filter

    pipe.set_screen(total_filter)  

    return pipe


 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.pipe_output = pipeline_output('my_pipeline').dropna()
    context.pipe_output['abs_beta'] = abs(context.pipe_output['beta'])
    context.pipe_output = context.pipe_output.sort_values('abs_beta')
    # row_count = context.pipe_output.shape[0]
    context.longs = context.pipe_output.loc[context.pipe_output['mom_5']>1][1:101:2]
    context.shorts = context.pipe_output.loc[context.pipe_output['mom_5']<1][0:100:2]
    # context.ranked = context.pipe_output["beta"].abs().rank().order()
    # print context.pipe_output
    # a = context.pipe_output.head()
    print context.pipe_output
    # context.longs = context.ranked[context.ranked['mom_5']>1].head(50)
    # context.shorts = context.ranked[context.ranked['mom_5']<1].tail(50)
    # context.longs = context.ranked[:50]
    # context.shorts = context.ranked[-50:]
    # The pipe character "|" is the pandas union operator
    # update_universe(context.longs.index | context.shorts.index)
    print context.longs.index[:3]
    print context.shorts.index[:3]

def recover_period(data):
    close = data.history(sid(8554),'close', 120, '1d')
    sma5 = ta.SMA(close, 5)[-1]
    # print sma5
    sma20 = ta.SMA(close, 20)[-1]
    sma60 = ta.SMA(close, 60)[-1]
    # print sma5
    # print sma20
    # print sma60
    short_ratio = sma5/sma20 if sma5/sma20 else 1
    mid_ratio = sma20/sma60 if sma20/sma60 else 1
    # long_ratio = sma5/sma60 if sma5/sma60 else 1
    if (short_ratio > 1) and (mid_ratio > 1):
        return True
    else:
        return False

def daily_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    size = min(len(context.longs), len(context.shorts))
    # Condition to long
    i = 0
    for security in context.longs.index:
        if data.can_trade(security) and i < size and context.account.leverage <= 1.5:
            order_target_percent(security, 0.5 / size) 
            i += 1
    # Condition to short
    j = 0
    for security in context.shorts.index:
        if data.can_trade(security) and j < size and context.account.leverage <= 1.5:
            order_target_percent(security, -0.5 / size)
            j += 1

    # Condition to sell
    # Recover Period
    if not recover_period(data):
        for security in context.portfolio.positions:
            hist = data.history(security, 'close', 5, '1d')
            mom5 = hist[-1]/hist[0]
            hold = context.portfolio.positions[security]
            if (mom5 < 1 and hold.amount > 0):
              order_target_percent(security, 0)
            elif (mom5 > 1 and hold.amount < 0):
              order_target_percent(security, 0)
    
    print "Called daily rebalance"


def weekly_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    print "Called weekly rebalance"



def monthly_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    print "Called monthly rebalance"
    



def record_vars(context, data):
    """
    Plot variables at the end of each day. Use schedule_function()
    """
    # beta1 = 0
    # for security in context.portfolio.positions:
    #     tmp = (RollingLinearRegressionOfReturns(security, returns_length=60,
    # regression_length=60,))
    #     beta1 += tmp.beta

    record(lever=context.account.leverage,
           num_pos=len(context.portfolio.positions))#,
          # cash=context.portfolio.cash,
          # pnl=context.portfolio.pnl)
 


def handle_data(context,data):
    """
    Called every minute.
    """
    record_vars(context, data);



"""
Called once at the start of the algorithm.
"""   
def initialize(context):

    # Set Commission
    set_commission(commission.PerShare(cost=0.0075, min_trade_cost=1))
    # Set Slippage
    set_slippage(slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))
    # Set Benchmark: SP500
    set_benchmark(sid(8554))

    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')

    # Rebalances
    # schedule_function(daily_rebalance, \
    #     date_rules.every_day(), time_rules.market_close()) 
    schedule_function(daily_rebalance, \
        date_rules.week_start(), time_rules.market_open())

    # schedule_function(weekly_rebalance, \
    #     date_rules.week_start(), time_rules.market_open(hours=1))

    schedule_function(monthly_rebalance, \
        date_rules.month_start(days_offset=0), time_rules.market_open(), half_days=True)
