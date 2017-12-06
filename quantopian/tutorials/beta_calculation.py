'''
Three inputs to understand beta calculation.

Try with different amounts of starting capital. See results table below.

In the contest, if going for top-allowed leverage of 3 using margin,
  you would see beta run higher than the same securities without margin.

Investing only in SPY, one might expect a beta of 1.0 since the investment exactly matches
  the movements of the market (SPY). Useful while writing code?
  And yet, to an investor, is it only overall beta per initial capital that matters?

'''
import pandas as pd

def initialize(context):
    set_commission(commission.PerShare(cost=0))
    context.spy = sid(8554)
    context.beta_df1 = pd.DataFrame([], columns = ['wild', 'spy'])
    context.beta_df2 = pd.DataFrame([], columns = ['wild', 'spy'])
    context.beta_df3 = pd.DataFrame([], columns = ['wild', 'spy'])
    schedule_function(trade, date_rules.every_day(), time_rules.market_open())

def before_trading_start(context, data):
    c = context

    value1 = c.portfolio.portfolio_value
    value2 = c.portfolio.returns + 1
    value3 = c.portfolio.positions_value

    if not (value1 and value2 and value3): return    # skip any 0's

    # Beta calc prep
    c.beta_df1 = c.beta_df1.append({
        'wild': value1,
        'spy' : data.current(c.spy, 'price')}, ignore_index=True).ix[-252:]

    c.beta_df2 = c.beta_df2.append({
        'wild': value2,
        'spy' : data.current(c.spy, 'price')}, ignore_index=True).ix[-252:]

    c.beta_df3 = c.beta_df3.append({
        'wild': value3,
        'spy' : data.current(c.spy, 'price')}, ignore_index=True).ix[-252:]

    if len(c.beta_df1) < 3: return
    record(beta_portfolio = calc_beta1(c, data))
    record(beta_returns   = calc_beta2(c, data))
    record(beta_positions = calc_beta3(c, data))

def calc_beta1(context, data):
    changes = context.beta_df1.pct_change()
    return changes.wild.cov(changes.spy) / changes.spy.var()

def calc_beta2(context, data):
    changes = context.beta_df2.pct_change()
    return changes.wild.cov(changes.spy) / changes.spy.var()

def calc_beta3(context, data):
    changes = context.beta_df3.pct_change()
    return changes.wild.cov(changes.spy) / changes.spy.var()

def trade(context, data):
    if not context.portfolio.positions:
        order(context.spy, 10)
        #order(sid(39840), 10)    # TSLA or others to try
        print data.current(context.spy, 'price')

'''
Results for various inputs
2010-06-30 to 2017-06-14
10 shares of SPY where the price is $104.00 at start.
(Margin of 818 with initial capital at 104).

Beta inputs:
    ==> returns (the Quantopian method) or portfolio_value
            cash            Quantopian beta         beta calculated
                104         3.73                     3.74
                1040         .97                      .98
                10400        .13                      .13
    ==> positions_value
            cash            Quantopian beta         beta calculated
                104         3.73                     1.0
                1040         .97                     1.0
                10400        .13                     1.0
'''
"""
# Zipline beta
def estimateBeta(priceY,priceX):  
    algorithm_returns = (priceY/priceY.shift(1)-1).dropna().values  
    benchmark_returns = (priceX/priceX.shift(1)-1).dropna().values  
    if len(algorithm_returns) <> len(benchmark_returns):  
        minlen = min(len(algorithm_returns), len(benchmark_returns))  
        if minlen > 2:  
            algorithm_returns = algorithm_returns[-minlen:]  
            benchmark_returns = benchmark_returns[-minlen:]  
        else:  
            return 1.00  
    returns_matrix = np.vstack([algorithm_returns, benchmark_returns])  
    C = np.cov(returns_matrix, ddof=1)  
    algorithm_covariance = C[0][1]  
    benchmark_variance = C[1][1]  
    beta = algorithm_covariance / benchmark_variance

    return beta
"""