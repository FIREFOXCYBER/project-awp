from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters import Q1500US 

def initialize(context):
    # In our example, we're looking at Apple. 
    context.security = sid(24)

    # Specify that we want the 'rebalance' method to run once a day
    schedule_function(rebalance, date_rule=date_rules.every_day())

"""
Rebalance function scheduled to run once per day (at market open).
"""
def rebalance(context, data):
    # To make market decisions, we're calculating the stock's 
    # moving average for the last 5 days.

    # We get the price history for the last 5 days. 
    price_history = data.history(
        context.security,
        fields='price',
        bar_count=5,
        frequency='1d'
    )

    # Then we take an average of those 5 days.
    average_price = price_history.mean()
    
    # We also get the stock's current price. 
    current_price = data.current(context.security, 'price') 
    
    # If our stock is currently listed on a major exchange
    if data.can_trade(context.security):
        # If the current price is 1% above the 5-day average price, 
        # we open a long position. If the current price is below the 
        # average price, then we want to close our position to 0 shares.
        if current_price > (1.01 * average_price):
            # Place the buy order (positive means buy, negative means sell)
            order_target_percent(context.security, 1)
            log.info("Buying %s" % (context.security.symbol))
        elif current_price < average_price:
            # Sell all of our shares by setting the target position to zero
            order_target_percent(context.security, 0)
            log.info("Selling %s" % (context.security.symbol))
    
    # Use the record() method to track up to five custom signals. 
    # Record Apple's current price and the average price over the last 
    # five days.
    record(current_price=current_price, average_price=average_price)
