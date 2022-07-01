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


"""
Liquidation process:
    1. Off-chain worker trigger liquidation and vault seizes collateral
    2. A third party can now burn iBTC to receive the collateral
        2.1 Buy iBTC
        2.2 Burn iBTC
        2.3 Receive collateral
    3. (Optional) Swap collateral into other currency


Modelling:
    1. Seizure of collateral: Nothing
    2. Liquidating the collateral
        2.1 Buy iBTC: Model the liquidity needed to buy the total amount if iBTC oustanding
            2.1.1 Model the slippage of DEX
            2.1.2 Model the slippage of a CEX # is it fair to assume that
            
"""


# %%
from data_request import Token, Token_Pair, Data_Request
from analysis import Analysis
from simulation import Simulation
from matplotlib import pyplot as plt

quote_currency = Token("btc", "BTC")
base_currency = Token("acala-dollar", "aUSD")

pair = Token_Pair(base_currency, quote_currency)
pair.get_prices()
pair.calculate_returns()

simple_analysis = Analysis(pair)
simple_analysis.plot_returns("Percentage", "Performance")


# %%
sim = Simulation(pair, strategy="GMB")
sim.simulate(steps=365, maturity=3, n_simulations=5)


# %%
# plot all paths for the both processes
length = sim.paths.shape[1]
f, subPlots = plt.subplots(sharex=True)
plt.rcParams['figure.figsize'] = [16.0, 10.0]
f.suptitle('Path simulations n=' + str(length))
subPlots.set_title('Geometric Brownian Motion')

for i in range(length):
    path = sim.paths.iloc[:, i]
    subPlots.plot(path)

# %%
