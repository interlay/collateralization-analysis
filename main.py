# 1. Initialize a token pair
#     1.1 Get price data for the token pair
#       - Query data
#       - Parse data into data frame
#
# 2. Initialize a strategy
# 3. Initialize a simulation
# 3.1. Add the token pair to the simulation
# 3.2 Add the strategy to the simulation
# 3.3 Run the simulation
#%%
from data_request import Token, Token_Pair, Data_Request
from analysis import Analysis

quote_currency = Token("USD", "USD")
base_currncy = Token("kintsugi","KINT")

pair = Token_Pair(base_currncy, quote_currency)
pair.get_prices(start_date="2022-01-01")
pair.calculate_returns()

simple_analysis = Analysis(pair)
#%%
simple_analysis.plot_returns("Percentage", "Performance")


# %%
