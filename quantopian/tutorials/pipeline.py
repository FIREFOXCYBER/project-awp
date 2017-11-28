'''
	2. Creating a pipeline
'''
from quantopian.pipeline import Pipeline 
def make_pipeline():
    return Pipeline()

my_pipe = make_pipeline()


from quantopian.research import run_pipeline
# run_pipeline returns a panda dataframe
result = run_pipeline(my_pipe, '2015-05-05', '2015-05-05')
result.head()

'''
	3. Factors
'''
# Factors are the most commonly-used term, 
# representing the result of any computation producing a numerical result. 
# Factors require a column of data as well as a window length as input.

# https://www.quantopian.com/help#initializing_a_pipeline
# Built-in dataset, USEquityPricing contains {open, close, high, low, volume}
from quantopian.pipeline.data.builtin import USEquityPricing 
# factors from 'built-in'
# https://www.quantopian.com/help#built-in-factors
from quantopian.pipeline.factors import SimpleMovingAverage

''' Creating a factor: Just like create a functions '''

# input: value
# window_length: how many values
mean_close_10 = SimpleMovingAverage(
    inputs=[USEquityPricing.close],
    window_length=10
)

''' Adding a factor to a pipeline '''
def make_pipeline():

  # Make factor
  mean_close_10 = SimpleMovingAverage(
      inputs=[USEquityPricing.close],
      window_length=10
  )
  # Call factor in pipeline (just like call functions)
  return Pipeline(
      columns={
          '10_day_mean_close': mean_close_10
    }
  )

# Call run_pipeline()
result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
result.head()

# Add a factor to existed pipeline
my_pipe = Pipeline()
f1 = SimpleMovingAverage(...)
my_pipe.add(f1) # using 'add()' on pipeline

''' Latest '''
def make_pipeline():

    mean_close_10 = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=10
    )
    # This add another column for pipeline
    latest_close = USEquityPricing.close.latest

    return Pipeline(
        columns={
            '10_day_mean_close': mean_close_10,
            'latest_close_price': latest_close
        }
    )
''' Default Inputs '''
# Some factors have default inputs that should never be changed.
# Volume Weighted Average Price
from quantopian.pipeline.factors import VWAP
vwap = VWAP(window_length=10) # don't need 'input=' here

'''
	4. Combining Factors
'''

''' Combining Factors '''
# Using arithemetics
f1 = SomeFactor()
f2 = SomeOtherFactor()
average = (f1+f2) / 2.0
# e.g. Percent_difference (by combining two factors)
def make_pipeline():

    mean_close_10 = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=10
    )
    mean_close_30 = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=30
    )

    percent_difference = (mean_close_10 - mean_close_30) / mean_close_30

    return Pipeline(
        columns={
            'percent_difference': percent_difference
        }
    )
result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
result.head()

''' 
	5. Filters
'''
# A filter is a function from an asset and a moment in time to a boolean

# Filters are used for narrowing down the set of securities 
# included in a computation or in the final output of a pipeline. 
# There are two common ways to create a Filter: 
# comparison operators and Factor/Classifier methods.

''' Comparison Operators '''
mean_close_10 = SimpleMovingAverage(
    inputs=[USEquityPricing.close],
    window_length=10
)
mean_close_30 = SimpleMovingAverage(
    inputs=[USEquityPricing.close],
    window_length=30
)
# Filtering
mean_crossover_filter = mean_close_10 < mean_close_30

''' Factor/Classifer Methods '''
last_close_price = USEquityPricing.close.latest
top_close_price_filter = last_close_price.top(200) # Filtering
# https://www.quantopian.com/help#quantopian_pipeline_factors_Factor
# https://www.quantopian.com/help#quantopian_pipeline_classifiers_Classifier

''' Dollar Volume Filter '''
def make_pipeline():

    mean_close_10 = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=10
    )
    mean_close_30 = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=30
    )

    # Filtering 1
    percent_difference = (mean_close_10 - mean_close_30) / mean_close_30
    # By default, AverageDollarVolume uses USEquityPricing.close 
    # and USEquityPricing.volume as its inputs, so we don't specify them.
    dollar_volume = AverageDollarVolume(window_length=30)

    # Filtering 2
    high_dollar_volume = (dollar_volume > 10000000)

    # Add filterred result to pipeline
    return Pipeline(
        columns={
            'percent_difference': percent_difference,
            'high_dollar_volume': high_dollar_volume
        },
    )
result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
result.head()

''' Applying A Screen '''
# filtering: gives condition
# screen: apply this condition
def make_pipeline():

  mean_close_10 = SimpleMovingAverage(
      inputs=[USEquityPricing.close],
      window_length=10
  )
  mean_close_30 = SimpleMovingAverage(
      inputs=[USEquityPricing.close],
      window_length=30
  )

  percent_difference = (mean_close_10 - mean_close_30) / mean_close_30

  dollar_volume = AverageDollarVolume(window_length=30)
  high_dollar_volume = (dollar_volume > 10000000)

  # Screen: ignore when return false 
  return Pipeline(
      columns={
          'percent_difference': percent_difference
      },
      screen=high_dollar_volume
  )
result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
print 'Number of securities that passed the filter: %d' % len(result)

''' Inverting A Filter ''' 
# Use ~ to invert (true <--> false)
low_dollar_volume = ~high_dollar_volume

'''
	6. Combining Filters
'''
''' Combining Filters '''
def make_pipeline():

    mean_close_10 = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=10
    )
    mean_close_30 = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=30
    )

    percent_difference = (mean_close_10 - mean_close_30) / mean_close_30

    dollar_volume = AverageDollarVolume(window_length=30)
    # percentile_between: Factor method returning a Filter
    high_dollar_volume = dollar_volume.percentile_between(90, 100)

    # above_20: a filter
    latest_close = USEquityPricing.close.latest
    above_20 = latest_close > 20

    # Combine filters
    is_tradeable = high_dollar_volume & above_20

    return Pipeline(
        columns={
            'percent_difference': percent_difference
        },
        # Apply the filter
        screen=is_tradeable
    )

result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
print 'Number of securities that passed the filter: %d' % len(result)

'''
	7. Masking
'''
''' Masking '''
# Masking: A factor/filter level 'screen' method
# Type: 
	# Factor Masking
	# Filter Masking

''' Masking Factors '''
# Dollar volume factor
dollar_volume = AverageDollarVolume(window_length=30)

# High dollar volume filter
high_dollar_volume = (dollar_volume > 10000000)

# Average close price factors
mean_close_10 = SimpleMovingAverage(
    inputs=[USEquityPricing.close],
    window_length=10,
    # mask: Apply filter in factor level, screen is apply filter in pipeline level
    mask=high_dollar_volume
)
mean_close_30 = SimpleMovingAverage(
    inputs=[USEquityPricing.close],
    window_length=30,
    mask=high_dollar_volume
)

# Relative difference factor
percent_difference = (mean_close_10 - mean_close_30) / mean_close_30


''' Masking Filters '''
def make_pipeline():

    # Dollar volume factor
    dollar_volume = AverageDollarVolume(window_length=30)

    # High dollar volume filter
    high_dollar_volume = dollar_volume.percentile_between(90,100)

    # Masking on filter
    # Top open securities filter (high dollar volume securities)
    top_open_price = USEquityPricing.open.latest.top(50, mask=high_dollar_volume)

    # Top percentile close price filter (high dollar volume, top 50 open price)
    high_close_price = USEquityPricing.close.latest.percentile_between(90, 100, mask=top_open_price)

    return Pipeline(
        screen=high_close_price
    )
result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
print 'Number of securities that passed the filter: %d' % len(result)

''' 
	8. Classifiers
'''
''' Classifiers '''
# A classifier is a function from an asset and a moment in time to a categorical output 
# such as a string or integer label.

from quantopian.pipeline.data import Fundamentals
# Since the underlying data of Fundamentals.exchange_id
# is of type string, .latest returns a Classifier
exchange = Fundamentals.exchange_id.latest

# Using Sector is equivalent to Fundamentals.morningstar_sector_code.latest
from quantopian.pipeline.classifiers.fundamentals import Sector
morningstar_sector = Sector()

''' Building Filters From Classifiers '''
# Classifier Methods:
# 		https://www.quantopian.com/help#quantopian_pipeline_classifiers_Classifier

# If we wanted a filter to select securities trading on the New York Stock Exchange, 
# we can use the eq method of our exchange classifier.
nyse_filter = exchange.eq('NYS')

''' Quantiles '''
# Classifiers can also be produced from various Factor methods. 
# The most general of these is the quantiles method, 
# which accepts a bin count as an argument. 
# The quantiles classifier assigns a label from 0 to (bins - 1) to 
# every non-NaN data point in the factor output. NaNs are labeled with -1. 
# Aliases are available for quartiles (quantiles(4)), quintiles (quantiles(5)), 
# and deciles (quantiles(10)). As an example, this is what a filter for the 
# top decile of a factor might look like
dollar_volume_decile = AverageDollarVolume(window_length=10).deciles()
top_decile = (dollar_volume_decile.eq(9))

# All together
def make_pipeline():

    exchange = Fundamentals.exchange_id.latest
    nyse_filter = exchange.eq('NYS')

    morningstar_sector = Sector()

    dollar_volume_decile = AverageDollarVolume(window_length=10).deciles()
    top_decile = (dollar_volume_decile.eq(9))

    return Pipeline(
        columns={
            'exchange': exchange,
            'sector_code': morningstar_sector,
            'dollar_volume_decile': dollar_volume_decile
        },
        screen=(nyse_filter & top_decile)
    )
result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
print 'Number of securities that passed the filter: %d' % len(result)
result.head()

'''
  9. Datasets
'''


# When building a pipeline, we need a way to identify the inputs to our computations. 
# The input to a pipeline computation is specified using DataSets and BoundColumns.

''' Datasets and BoundColumns '''
# DataSets: are simply collections of objects that tell the Pipeline API where and how to find the inputs to computations. 
#   An example of a DataSet that we have already seen is USEquityPricing.

# A BoundColumn: is a column of data that is concretely bound to a DataSet. 
# Instances of BoundColumns are dynamically created upon access to attributes of DataSets. 
# Inputs to pipeline computations must be of type BoundColumn. 
#   An example of a BoundColumn that we have already seen is USEquityPricing.close.

''' dtypes '''
# The dtype of a BoundColumn tells a computation what the type of the data will be 
# when the pipeline is run. 
#   For example, USEquityPricing has a float dtype so a factor may perform 
#   arithmetic operations on USEquityPricing.close (e.g. compute the 5-day mean). 

''' Pricing Data '''
# USEquityPricing.open
# USEquityPricing.high
# USEquityPricing.low
# USEquityPricing.close
# USEquityPricing.volume

''' Fundamental Data '''
# From 'morningstar'

''' Partner Data '''
# quantopian.pipeline.data.estimize (Estimize)
# quantopian.pipeline.data.eventVestor (EventVestor)
# quantopian.pipeline.data.psychsignal (PsychSignal)
# quantopian.pipeline.data.quandl (Quandl)
# quantopian.pipeline.data.sentdex (Sentdex)
# https://www.quantopian.com/help/fundamentals

'''
  10. Custom Factors
'''
# inputs are M x N numpy arrays, where M is the window_length and N is the number of securities (usually around ~8000 unless a mask is provided). *inputs are trailing data windows. Note that there will be one M x N array for each BoundColumn provided in the factor's inputs list. The data type of each array will be the dtype of the corresponding BoundColumn.
# out is an empty array of length N. out will be the output of our custom factor each day. The job of compute is to write output values into out.
# asset_ids will be an integer array of length N containing security ids corresponding to the columns in our *inputs arrays.
# today will be a pandas Timestamp representing the day for which compute is being called.
def compute(self, today, asset_ids, out, *inputs):
    ...

from quantopian.pipeline import CustomFactor, Pipeline
import numpy
class StdDev(CustomFactor):
    def compute(self, today, asset_ids, out, values):
        # Calculates the column-wise standard deviation, ignoring NaNs
        out[:] = numpy.nanstd(values, axis=0)
def make_pipeline():
    std_dev = StdDev(
        inputs=[USEquityPricing.close],
        window_length=5
    )

    return Pipeline(
        columns={
            'std_dev': std_dev
        }
    )
result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
result.head()    

''' Default Inputs '''
class TenDayMeanDifference(CustomFactor):
    # Default inputs.
    inputs = [USEquityPricing.close, USEquityPricing.open]
    window_length = 10
    def compute(self, today, asset_ids, out, close, open):
        # Calculates the column-wise mean difference, ignoring NaNs
        out[:] = numpy.nanmean(close - open, axis=0)
# Computes the 10-day mean difference between the daily open and close prices.
close_open_diff = TenDayMeanDifference()

# Computes the 10-day mean difference between the daily high and low prices.
high_low_diff = TenDayMeanDifference(inputs=[USEquityPricing.high, USEquityPricing.low])

''' Further Example '''
class Momentum(CustomFactor):
    # Default inputs
    inputs = [USEquityPricing.close]

    # Compute momentum
    def compute(self, today, assets, out, close):
        out[:] = close[-1] / close[0]

ten_day_momentum = Momentum(window_length=10)
twenty_day_momentum = Momentum(window_length=20)

positive_momentum = ((ten_day_momentum > 1) & (twenty_day_momentum > 1))

def make_pipeline():

    ten_day_momentum = Momentum(window_length=10)
    twenty_day_momentum = Momentum(window_length=20)

    positive_momentum = ((ten_day_momentum > 1) & (twenty_day_momentum > 1))

    std_dev = StdDev(
        inputs=[USEquityPricing.close],
        window_length=5
    )

    return Pipeline(
        columns={
            'std_dev': std_dev,
            'ten_day_momentum': ten_day_momentum,
            'twenty_day_momentum': twenty_day_momentum
        },
        screen=positive_momentum
    )
result = run_pipeline(make_pipeline(), '2015-05-05', '2015-05-05')
result.head()