# Pipeline Factors
- Momentum
- Beta
- Market Cap
- Moving Average
- Profit history

# before_trading()
- Filter securities from pipeline

# make_pipeline()
- Set up pipeline

# month_rebalance()
- calcualte pnl
- close all open order 

# daily_rebalance()
- calucalte buy condition, begin of day
- calcualte sell condition, end of day

# weekly_rebalance()
- close all open order 

# Other balance function

# record_var()
Record things like:
- My Beta (even though there is a system beta)
- Leverage

# initialize()
- attach_pipeline()
- set_commission(commission.PerShare(cost=0.0075, min_trade_cost=1))
- set_slippage(slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))
- schedule rebalances & record_var()


idea:
1. if abs(long-short) > 20, stop buying or selling
2. If short term beta is big, stop long stock
3. Recover period: recover from huge shock, there is a chance of over-transaction, which costs too much transaction fees
4. Shock: works good, which is a strong momentum
5. recover period is a weak momentum, need to detect it too

Portfolio beta: Weighted Average Beta of each equity (weight is average total value during a period)



https://www.quantopian.com/posts/pipeline-calculating-beta
https://www.quantopian.com/posts/beta-to-spy
