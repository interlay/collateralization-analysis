from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation


quote_currency = Token("usd", "USD")
base_currency = Token("bitcoin", "BTC")

token_pair = Token_Pair(base_currency, quote_currency)
token_pair.get_prices(start_date="2017-07-01", inverse=True)
token_pair.calculate_returns()

print(f"{token_pair.base_token.ticker}/{token_pair.quote_token.ticker} had an annualized std of {token_pair.returns.std()[0] *365**0.5}")
print(f"{token_pair.base_token.ticker}/{token_pair.quote_token.ticker} had an annualized mean return of {token_pair.calculate_mean_return()}")

# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 7 days and hourly steps each
# and assume a normal distribution (GBM) with the mean and std of the pair over the past 5 years
sim = Simulation(token_pair, strategy="GBM")
sim.simulate(steps=24,
             maturity=7,
             n_simulations=10_000,
             initial_value=1,
             sigma=token_pair.returns.std()[0],
             mu=token_pair.calculate_mean_return(type="arithmetic", standardization_period="daily"))


# Analize the results
# Initialize the analysis
simple_analysis = Analysis(sim)

# This gives us the secure threshold multiplier, stating that:
# The collateral/debt ratio will fall below 1 only with a 0.1% chance in 7 days or...
# This assumes no premium redeem, additional collateralization or liquidation.
liquidation_threshold_margin = simple_analysis.get_threshold_multiplier(alpha=0.999) # <- this can be changed ofc 
premium_redeem_threshold_margin = simple_analysis.get_threshold_multiplier(alpha=0.90) # <- this can be changed ofc 

print(f"The estimated liquidation threshold is ~{int(liquidation_threshold_margin * 100)}% of the debt value")
print(f"The estimated premium redeem threshold is ~{int(liquidation_threshold_margin * premium_redeem_threshold_margin * 100)}% of the debt value")


# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 21 days and hourly steps each
# and assume a normal distribution (GBM) with the mean and std of token_pair over the past 5 years
sim = Simulation(token_pair, strategy="GBM")
sim.simulate(steps=24,
             maturity=21,
             n_simulations=10_000,
             initial_value=1,
             sigma=token_pair.returns.std()[0],
             mu=token_pair.calculate_mean_return(type="arithmetic", standardization_period="daily"))


# Analize the results
# Initialize the analysis
simple_analysis = Analysis(sim)

# This gives us the secure threshold multiplier, stating that:
# The collateral/debt ratio will fall below the liquidation_threshold_margin with a 10% chance in 21 days or...
# This assumes no premium redeem, additional collateralization or liquidation.
secure_threshold_margin = simple_analysis.get_threshold_multiplier(alpha=0.90) # <- this can be changed ofc 

print(f"The estimated secure threshold is ~{int(liquidation_threshold_margin * secure_threshold_margin * 100)}% of the debt value")