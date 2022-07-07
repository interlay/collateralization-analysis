# 1. Initialize a token btc_pair
#     1.1 Get price data for the token btc_pair
#       - Query data
#       - Parse data into data frame
#
# 2. Initialize a strategy
# 3. Initialize a simulation
# 3.1. Add the token btc_pair to the simulation
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

#TODO
Modelling:
    1. Seizure of collateral: Nothing
    2. Liquidating the collateral
        2.1 Buy iBTC: Model the liquidity needed to buy the total amount if iBTC oustanding
            2.1.1 Model the slippage of DEX
            2.1.2 Model the slippage of a CEX # is it fair to assume that
"""


# %%
from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation
from data.market import Automted_Market_Maker


quote_currency = Token("usd", "USD")
base_currency = Token("acala-dollar", "aUSD")

ausd_pair = Token_Pair(base_currency, quote_currency)
ausd_pair.get_prices()
ausd_pair.calculate_returns()
print(f"aUSD/USD had an annualized std of {ausd_pair.returns.std()[0] *365**0.5}")
print(f"aUSD/USD had an annualized mean return of {ausd_pair.calculate_mean_return()}")
# We can disregard the mean return as it is assumed to be 0 for stable coins due to arbitrage
# We have to take into consideration the standard deviation of the price, which we will
# add to the standard deviation of BTC

#%%
# BTC is the debt in the system and if BTC increases in price, the over-collateralization ratio drops
# To model this, we get the inverse price to have BTC as quote currency
# If we select the n-th worst trajectories of the inverse price,
# it's equivalent to the n-th best price appreciation.
# We choose a 5 year period to get a decent sample period with 3 bull runs & crashes
quote_currency = Token("usd", "USD")
base_currency = Token("bitcoin", "BTC")

btc_pair = Token_Pair(base_currency, quote_currency)
btc_pair.get_prices(start_date="2017-07-01", inverse=True)
btc_pair.calculate_returns()

print(f"USD/BTC had an annualized std of {btc_pair.returns.std()[0] *365**0.5}")
print(f"USD/BTC had an annualized mean return of {btc_pair.calculate_mean_return()}")

# %%
# We adjust the variance by adding the covariance of the aUSD/USD pair.
corr = ausd_pair.returns.corrwith(btc_pair.returns)
cov = corr * (btc_pair.returns.std()[0] *365**0.5) * (ausd_pair.returns.std()[0] *365**0.5)
# daily var scaled to a year, add 2*covariance and take the square root to get the std
adj_btc_std = (btc_pair.returns.var()[0] *365 + 2 * cov) ** 0.5

# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 1 year and 365 trading days
# and assume a normal distribution (GBM) with the mean and std of bitcoin over the past 5 years
sim = Simulation(btc_pair, strategy="GBM")
sim.simulate(steps=365,
             maturity=1,
             n_simulations=10_000,
             initial_value=1,
             sigma=adj_btc_std[0],
             mu=btc_pair.calculate_mean_return(type="arithmetic"))


# %%
# Analize the results
# Initialize the analysis and plot all paths
simple_analysis = Analysis(sim)
simple_analysis.plot_returns("Percentage", "Performance", type="line")

# This gives us the secure threshold multiplier, stating that:
# The collateral/debt ratio will fall below 1 only with a 10% chance in a year or...
# We should see this happening once every ~10 years.
# This assumes no premium redeem, additional collateralization or liquidation.
secure_threshold = simple_analysis.get_threshold_multiplier(alpha=0.90) # <- this can be changed ofc 

print(f"The estimated liquidation threshold is ~{int(secure_threshold * 100)}% of the debt value")

# %%
# This time we do the same process on a intraday basis
# We adjust the variance by adding the covariance of the aUSD/USD pair.
corr = ausd_pair.returns.corrwith(btc_pair.returns)
cov = corr * btc_pair.returns.std()[0] * ausd_pair.returns.std()[0]
# daily var scaled to a year, add 2*covariance and take the square root to get the std
adj_btc_std = (btc_pair.returns.var()[0] + 2 * cov) ** 0.5

# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 10 days and 24 hours each
# and assume a normal distribution (GBM) with the mean and std of bitcoin over the past 5 years
sim = Simulation(btc_pair, strategy="GBM")
sim.simulate(steps=24,
             maturity=10,
             n_simulations=10_000,
             initial_value=1,
             sigma=adj_btc_std[0],
             mu=btc_pair.calculate_mean_return(type="arithmetic", standardization_period="daily"))


# %%
# Analize the results
# Initialize the analysis and plot all paths
simple_analysis = Analysis(sim)
simple_analysis.plot_returns("Percentage", "Performance", type="line")

# This gives us the secure threshold multiplier, stating that:
# The collateral/debt ratio will fall below 1 only with a 0.1% chance in 10 days or...
# This assumes no premium redeem, additional collateralization or liquidation.
liquidation_threshold = simple_analysis.get_threshold_multiplier(alpha=0.999) # <- this can be changed ofc 

print(f"The estimated liquidation threshold is ~{int(liquidation_threshold * 100)}% of the debt value")



#%%
##################### [WIP] ######################
# create an AMM to simulate slippage
start_price = sim.token_pair.prices.iloc[0, 0]
TVL = 10_000_000
amm = Automted_Market_Maker(
    btc_pair.base_token,
    btc_pair.quote_token,
    base_token_amount=TVL / 2 / start_price,
    quote_token_amount=TVL / 2,
)

print(f"The amm has {amm.base_token_amount} {amm.base_token.ticker}")
print(f"The amm has {amm.quote_token_amount} {amm.quote_token.ticker}\n")

trade_amount_base_token = 60
slippage = amm.calculate_params(trade_amount_base_token)

print(
    f"A trade of {trade_amount_base_token} {amm.base_token.ticker} would take a slippage of {slippage*100}%"
)

# %%
# add liquidity

amm.add_liquidity(5_000_000)
print(f"The amm has {amm.quote_token_amount} {amm.quote_token.ticker}")
print(f"The amm has {amm.base_token_amount} {amm.base_token.ticker}\n")


#%%
# remove liquidity
amm.remove_liquidity(200_000)
print(f"The amm has {amm.quote_token_amount} {amm.quote_token.ticker}")
print(f"The amm has {amm.base_token_amount} {amm.base_token.ticker}\n")


# %%
