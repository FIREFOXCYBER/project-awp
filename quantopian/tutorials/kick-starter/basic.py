# https://www.quantopian.com/help
############################################- LECTURE 1 -###########################################
'''
Two important functions
    initialize(): Called when the program is started (like 'main()' in C++). Only be called once.
    handle_data(): Called once #per minute# during simulation or living-trading in events (refers to as 'bars')
'''
def initialize(context):
    # Reference to AAPL
    context.aapl = sid(24)

def handle_data(context, data):
    # Position 100% of our portfolio to be long in AAPL
    order_target_percent(context.aapl, 1.00)

############################################- LECTURE 2 -###########################################
'''
    - initialize() is required in each algorithm, while handle_data() and before_trading_start() is optional
    - initialize():
        - Is called exactly once when algo starts and require 'context' as input
        - content: an augmented Python library used for maintaining state during backtest or living trading. To access properties, use 'context.some_property'
    - handle_data():
        - Is called once at the end of each minute and requires 'context' and 'data' as input
        - 'context' is same as in 'initialize()'
    - before_trading_start():
        - Is called once per day before the market opens and requires `context` and `data` as input
        - Common usage: selecting securities to order.
'''
def initialize(context):
    context.message = 'hello'

def handle_data(context, data):
    print context.message

############################################- LECTURE 3 -###########################################
'''
    - pipeline: Advanced algo to select securities to trade dynamically
    - mannually pick securities: 
        - sid() 
        - symbols(): not robust if not set look up date
        - sid(24) == symbol('AAPL')
        - symbol(): For 1 security
        - symbols(): For multiply securities
'''
# Mannually pick securities
set_symbol_lookup_date('2008-01-01')
symbols('amzn', 'csco')

############################################- LECTURE 4 -###########################################
'''
    - order_target_percent(security, percent)
        
'''
# Order 50% of our portfolio value worth of AAPL
order_target_percent(sid(24), 0.5)
# Short with 50% of our portfolio value worth of AAPL
order_target_percnet(sid(24), -0.5)
# The following example takes a long position in Apple stock worth 60% of our portfolio value, and takes a short position in the SPY ETF worth 40% of our portfolio value:
def initialize(context):
    context.aapl = sid(24)
    context.spy = sid(8554)

def handle_data(context, data):
    # Note: data.can_trade() is explained in the next lesson
    if data.can_trade(context.aapl): # check whether security can be traded
        order_target_percent(context.aapl, 0.60)
    if data.can_trade(context.spy):
        order_target_percent(context.spy, -0.40)

############################################- LECTURE 5 -###########################################
'''
    - 'data' object: data is available in handle_data() and before_trading_start() and any other scheduled functions
    - data.current(security, method)
    - method: price, open, high, low, close, volume
    - data.can_trade(): determine if asset is tradable
'''
# get current price and return pandas series
data.current(sid(24), 'price')
# get low & high price and get pandas dataframe
data.current([sid(24), sid(8554)], ['low', 'high'])
# Return true if security can be traded
data.can_trade(sid(24))

############################################- LECTURE 6 -###########################################
'''
    - history(): get trailing windows of historical pricing or volume data
'''
# Get the 10-day trailing price history of AAPL in the form of a Series.
hist = data.history(sid(24), 'price', 10, '1d')
# Mean price over the last 10 days.
mean_price = hist.mean()
# Last 10 complete days
data.history(sid(8554), 'volume', 11, '1d')[:-1].mean()
# Get the last 5 minutes of volume data for each security in our list.
hist = data.history([sid(24), sid(8554), sid(5061)], 'volume', 5, '1m')
# Calculate the mean volume for each security in our DataFrame.
mean_volumes = hist.mean(axis=0)
# Low and high minute bar history for each of our securities.
hist = data.history([sid(24), sid(8554), sid(5061)], ['low', 'high'], 5, '1m')
# Calculate the mean low and high over the last 5 minutes
means = hist.mean()
mean_lows = means['low']
mean_highs = means['high']
# In IDE
def initialize(context):
    # AAPL, MSFT, SPY
    context.security_list = [sid(24), sid(8554), sid(5061)]

def handle_data(context, data):
    hist = data.history(context.security_list, 'volume', 10, '1m').mean()
    print hist.mean()

############################################- LECTURE 7 -###########################################
'''
    - US Equities Market: 9:30AM - 4PM
    - schedule_function(): allows us to schedule custom functions at regular intervals and allows to specify interday frequency and intraday timing.
    - Skipped market half days: schedule_function(half_days=False)
'''
# Schedules a function called rebalance() to run once per day, one hour after market open (usually 10:30AM ET).
# rebalance: A function requiring 'context' and 'data'
# time_rules.market_open(): run in the 9:30AM ET minute bar if we selected US equity calendar
schedule_function(func=rebalance,
                  date_rules=date_rules.every_day(),
                  time_rules=time_rules.market_open(hours=1))
# run a custom function weekly_trades(), on the last trading day of each week, 30 minutes before market close. We can use:
schedule_function(weekly_trades, 
		  date_rules.week_end(), 
		  time_rules.market_close(minutes=30))

# Long SPY at the beginning of the week, and closes out the position at 3:30PM on the last day of week
def initialize(context):
    context.spy = sid(8554)
    schedule_function(open_positions, date_rules.week_start(), time_rules.market_open())
    schedule_function(close_positions, date_rules.week_end(), time_rules.market_close(minutes=30))
# Long 10% of our portfolio value's SPY
def open_positions(context, data):
    order_target_percent(context.spy, 0.10)

def close_positions(context, data):
    order_target_percent(context.spy, 0)

############################################- LECTURE 8 -###########################################
'''
'''
# To close out all of our open positions. To do so, we can iterate over the keys in context.portfolio.positions, and close out each position:
for security in context.portfolio.positions:
  order_target_percent(security, 0)

# The following example plots the number of long positions in our portfolio as a series called 'num_long', and the number of short positions as 'num_short'.
def initialize(context):
    context.aapl = sid(24)
    context.spy = sid(8554)

    schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())
    schedule_function(record_vars, date_rules.every_day(), time_rules.market_close())

def rebalance(context, data):
    order_target_percent(context.aapl, 0.50)
    order_target_percent(context.spy, -0.50)

def record_vars(context, data):

    long_count = 0
    short_count = 0

    for position in context.portfolio.positions.itervalues():
        if position.amount > 0:
            long_count += 1
        if position.amount < 0:
            short_count += 1

    # Plot the counts
    record(num_long=long_count, num_short=short_count)

############################################- LECTURE 9 -###########################################
'''
    - Slippage is where our backtester calculates the realistic impact of your orders on the execution price you receive.
    - Slippage: Slippage is where a simulation estimates the impact of orders on the fill rate and execution price they receive. 
    - Slippage must be defined in the initialize method. It has no effect if defined elsewhere in your algorithm. If you do not specify a slippage method, slippage defaults to VolumeShareSlippage(volume_limit=0.025, price_impact=0.1) (you can take up to 2.5% of a minute's trade volume).
'''
# Slippage
# slippage.VolumeShareSlippage()
# volume_limit: Meaning the percentage of my order in each minute's total trades by entire market, e.g. if there are 1000 share is traded in each next 3 minutes (total 3000), and if placed a 60 shares order, then my order will be filled in 25, 25, 10 and be finished in the 3rd minute after I placed the order
# price_impact: Price impact is how large of an impact you order will have on the backtester's price calculation. What we fill in function is a constant, 
# and the actual price impact: Price_Impact_constant * volume_limit^2
# In previous example a 25 shares order will impact: 0.025^2*0.1, given price_impact = 0.1
set_slippage(slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))
# Commission
# commission.PerShare(cost_per_share, fixed_cost_for_each_trade)
set_commission(commission.PerShare(cost=0.001, min_trade_cost=1))
###########################################- LECTURE 10 -###########################################
'''
    - If an order takes more than one minute to fill, it's considered open until it fills. When placing new orders, it's sometimes necessary to consider open orders.
    - get_open_orders(): returns a dict of open orders keyed by assets, this can help over-ordering
'''
def initialize(context):
    # Relatively illiquid stock.
    context.xtl = sid(40768)

def handle_data(context, data):
    # Get all open orders.
    open_orders = get_open_orders()

    if context.xtl not in open_orders and data.can_trade(context.xtl):
        order_target_percent(context.xtl, 1.0)

###########################################- LECTURE 11 -###########################################
def initialize(context):
    """
    initialize() is called once at the start of the program. Any one-time
    startup logic goes here.
    """

    # An assortment of securities from different sectors:
    # MSFT, UNH, CTAS, JNS, COG
    context.security_list = [sid(5061), sid(7792), sid(1941), sid(24556), sid(1746)]

    # Rebalance every Monday (or the first trading day if it's a holiday)
    # at market open.
    schedule_function(rebalance,
                      date_rules.week_start(days_offset=0),
                      time_rules.market_open())

    # Record variables at the end of each day.
    schedule_function(record_vars,
                      date_rules.every_day(),
                      time_rules.market_close())

def compute_weights(context, data):
    """
    Compute weights for each security that we want to order.
    """

    # Get the 30-day price history for each security in our list.
    hist = data.history(context.security_list, 'price', 30, '1d')

    # Create 10-day and 30-day trailing windows.
    prices_10 = hist[-10:]
    prices_30 = hist

    # 10-day and 30-day simple moving average (SMA)
    sma_10 = prices_10.mean()
    sma_30 = prices_30.mean()

    # Weights are based on the relative difference between the short and long SMAs
    raw_weights = (sma_30 - sma_10) / sma_30

    # Normalize our weights
    normalized_weights = raw_weights / raw_weights.abs().sum()

    # Determine and log our long and short positions.
    short_secs = normalized_weights.index[normalized_weights < 0]
    long_secs = normalized_weights.index[normalized_weights > 0]

    log.info("This week's longs: " + ", ".join([long_.symbol for long_ in long_secs]))
    log.info("This week's shorts: " + ", ".join([short_.symbol for short_ in short_secs]))

    # Return our normalized weights. These will be used when placing orders later.
    return normalized_weights

def rebalance(context, data):
    """
    This function is called according to our schedule_function settings and calls
    order_target_percent() on every security in weights.
    """

    # Calculate our target weights.
    weights = compute_weights(context, data)

    # Place orders for each of our securities.
    for security in context.security_list:
        if data.can_trade(security):
            order_target_percent(security, weights[security])

def record_vars(context, data):
    """
    This function is called at the end of each day and plots our leverage as well
    as the number of long and short positions we are holding.
    """

    # Check how many long and short positions we have.
    longs = shorts = 0
    for position in context.portfolio.positions.itervalues():
        if position.amount > 0:
            longs += 1
        elif position.amount < 0:
            shorts += 1

    # Record our variables.
    record(leverage=context.account.leverage, long_count=longs, short_count=shorts)
