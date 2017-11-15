## Strategy
### Global Macro
### Directional
### Event Driven
### Relative Value

## Measurement
### Sharpe Ratio

## Risk Management
### Risk Neutral
### VaR

## Approach
### Machine Learning
### Monte Carlo

## Quantopian
### Fundamentals
### Steps
- initialize()
- rebalance()
- before-trading-start()
- handle-data()
### Requirement
Low beta
High Sharpe > 1
Low drawdown

https://www.quantopian.com/data
https://www.quantopian.com/help
https://www.quantopian.com/help/fundamentals
http://sentdex.com/
https://www.quantopian.com/help#api-talib
https://www.quantopian.com/tutorials/algorithmic-trading-sentdex
https://www.quantopian.com/tutorials/pipeline#lesson1

Alphalens
pyfolio
pipeline
夏普指数越高，表明每单位风险的报酬越高，该投资工具越理想。
夏普比率低意味着基金是通过承担较高的风险获取收益，
夏普比率高意味着基金分散和降低非系统性风险的能力较高，收益率还有上升空间，
当夏普比率位于CML上方时，表明基金表现优于市场的总体表现。
(the beta) is the sensitivity of the expected excess asset returns to the expected excess market returns
max drawdown 选股，希望股票稳定
1. Annual Returns
2. Annual Volatility
3. Sharpe = Annual Return / Annual Volatility, higher is better
4. MAX Drawdown
5. Stability
6. Calmar Ratio = Annual Return / Max Drawdown, higher is better
7. Beta
8. Correlation
9. Sortino Ratio = Annual Return / STD(negative_returns), larger is better

1. Sell & Buy
2. Machine Learning
3. Sentiment
4. talib: technical analysis
5. Stock selection