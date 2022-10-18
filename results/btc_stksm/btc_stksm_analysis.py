# %%
import repackage
repackage.up(2)

import yaml
from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation
import pandas as pd
from datetime import datetime

with open('../../config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    
btc = Token("bitcoin", "BTC")
stKSM = Token("kusama", "KSM")

start_date = (datetime.today() - pd.Timedelta(
    config["analysis"]["historical_sample_period"])).strftime("%Y-%m-%d")

ksm_btc = Token_Pair(stKSM, btc)
ksm_btc.get_prices(start_date=start_date)
ksm_btc.calculate_returns()

#%%
# BTC is the debt in the system and if BTC increases in price, the over-collateralization ratio drops
# Vice versa, if the price of stKSM decreases, the collateralization ratio drops.
#
# To model this, we get the stKSM/BTC price to have stKSM as base currency (=collateral) and BTC as quote currency (=debt).
# We then select the n-th worst trajectorie of the price quotation.
#
# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 20,000 trajectories with a duration of 21
# and assume a normal distribution (GBM) with the mean of zero and std of the stKSM/BTC ksm_btc over the past ~3 years
sim = Simulation(ksm_btc, strategy="GBM")
sim.simulate(
    steps=1,
    maturity=config["analysis"]["thresholds"]["periods"]["safe_mint"],
    n_simulations=config["analysis"]["n_simulations"],
    initial_value=1,
    sigma=ksm_btc.returns.std()[0],
    mu=0,
)

#%%
# Analize the results
# Initialize the analysis
simple_analysis = Analysis(sim)

thresholds = {
    "liquidation": 
        {
            "analytical_threshold" : None,
            "historical_threshold" : None
        },
    "premium_redeem": 
        {
            "analytical_threshold" : None,
            "historical_threshold" : None
        },
    "safe_mint": 
        {
            "analytical_threshold" : None,
            "historical_threshold" : None
        }
}

#%%
# Before computing the thresholds, we're looking at the liquidity 
# The current TVL on Kintsugi is ~$1.75m USD locked in collateral.
# Starting with a 10% debt ceiling would mean to have a maximum of $175,000 worth of stKSM as collateral
# Assuming a worst case scenario where all stKSM is held by a single vault (or multiple vaults with similar liquidation price),
# would require a fire sale of the $175,000 stKSM.
# This would incure an estimated slippage of ~7% which means that all thresholds need to be adjusted accordingly

liquidity_adjustment = 1 / (1-0.07)
print(
    f"The estimated liquidity adjustment is ~{int(liquidity_adjustment * 100)}% of the debt value")



for key, threshold in thresholds.items():
    threshold["analytical_threshold"] = simple_analysis.get_threshold_multiplier(
        alpha=config["analysis"]["alpha"], at_step = config["analysis"]["thresholds"]["periods"][key]) * liquidity_adjustment
    hist_var = ksm_btc.prices.pct_change(config["analysis"]["thresholds"]["periods"][key]).dropna()
    hist_var = hist_var.sort_values("Price", ascending=False)
    threshold["historical_threshold"] = 1/(1+hist_var.iloc[int(len(hist_var) * config['analysis']['alpha']),][0]) * liquidity_adjustment
    
    print(f"The {key} threshold based on the analytical VaR for a confidence level of {config['analysis']['alpha']*100}% of stKSM/BTC over {config['analysis']['thresholds']['periods'][key]} is: {round(threshold['analytical_threshold'] *100,3)}%")
    print(f"The {key} threshold based on the historic VaR for a confidence level of {config['analysis']['alpha']*100}% of stKSM/BTC over {config['analysis']['thresholds']['periods'][key]} is: {round(threshold['historical_threshold'] *100,3)}% \n")

# %%
