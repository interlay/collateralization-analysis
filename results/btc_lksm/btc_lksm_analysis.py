# %%
import repackage

repackage.up(2)

import yaml
from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation
import pandas as pd
from datetime import datetime, timedelta

with open("../../config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

ksm, lksm, btc, usd = (
    Token("kusama", "KSM"),
    Token("liquid-ksm", "LKSM"),
    Token("bitcoin", "BTC"),
    Token("dollar", "USD"),
)

lksm_usd = Token_Pair(lksm, usd)
ksm_usd = Token_Pair(ksm, usd)
ksm_btc = Token_Pair(ksm, btc)
usd_btc = Token_Pair(
    btc, usd
)  # Note: the price query will be inverted to get the USD/BTC price

lksm_usd.get_prices()
lksm_usd.calculate_returns()

ksm_usd.get_prices(start_date="2019-09-19")
ksm_usd.calculate_returns()

ksm_btc.get_prices(start_date="2019-09-19")
ksm_btc.calculate_returns()

# Analysis of the variance and correlation of LKSM/KSM
print(
    f"The annualized volatility of LKSM for the period from {lksm_usd.returns.index[0]} \
    until {lksm_usd.returns.index[-1]} is {round(lksm_usd.returns.std()[0]*365**0.5,4)*100}%"
)

print(
    f"The annualized volatility of KSM for the period from {lksm_usd.returns.index[0]} \
    until {lksm_usd.returns.index[-1]} is {round(ksm_usd.returns.loc[lksm_usd.returns.index[0]:lksm_usd.returns.index[-1],].std()[0]*365**0.5,4)*100}% \n"
)

returns = pd.concat([lksm_usd.returns, ksm_usd.returns], axis=1).dropna()
returns.columns = ["LKSM Returns", "KSM Returns"]
corr = returns.corr()["LKSM Returns"]["KSM Returns"]
print(f"The correlation between LKSM and KSM is {round(corr,3)}")
print(
    f"The part of the variance unexplained by linear correlation between LKSM and KSM is {round((1-corr**2)*100,1)}%"
)

#%%
ksm_usd.get_prices(start_date="2019-09-19")
ksm_usd.calculate_returns()

usd_btc.get_prices(start_date="2019-09-19", inverse=True)
usd_btc.calculate_returns()

print(
    f"The annualized volatility of KSM/BTC for the period from {ksm_btc.returns.index[0]} \
    until {ksm_btc.returns.index[-1]} is {round(ksm_btc.returns.std()[0]*365**0.5,4)*100}%"
)

print(
    f"The annualized volatility of USD/BTC for the period from {usd_btc.returns.index[0]} \
    until {usd_btc.returns.index[-1]} is {round(usd_btc.returns.std()[0]*365**0.5,4)*100}%"
)

print(
    f"The annualized volatility of KSM/USD for the period from {ksm_usd.returns.index[0]} \
    until {ksm_usd.returns.index[-1]} is {round(ksm_usd.returns.std()[0]*365**0.5,4)*100}% \n"
)

#%%
# Checking the std to make a sanity check.
returns = pd.concat([usd_btc.returns, ksm_usd.returns], axis=1).dropna()
returns.columns = ["inverse BTC Returns", "KSM Returns"]
corr = returns.corr()["inverse BTC Returns"]["KSM Returns"]

print(f"The correlation between inverseBTC and KSM is {round(corr,3)}")
print(
    f"The part of the variance unexplained by linear correlation between BTC and KSM is {round((1-corr**2)*100,1)}%)"
)


returns.index = returns.index.astype(int) / 10**9
returns.reset_index(inplace=True)
returns.plot.scatter(
    x="inverse BTC Returns", y="KSM Returns", c="Date", colormap="viridis", sharex=False
)
#%%
# The graph indicates that the correlation between KSM and BTC increased over time
returns.set_index("Date", inplace=True)
returns.index = pd.to_datetime(returns.index.values, unit="s")

end_date = returns.index[-1]
while end_date in returns.index:
    start_date = (
        end_date - timedelta(config["analysis"]["historical_sample_period"])
        if end_date - timedelta(config["analysis"]["historical_sample_period"])
        in returns.index
        else returns.index[0]
    )
    print(
        f"""The correlation between KSM/USD and USD/BTC between {start_date} and {end_date} was {returns.loc[start_date:end_date,].corr()["inverse BTC Returns"]["KSM Returns"]}"""
    )
    print(
        f"The volatility of KSM/USD over the same period was {returns.loc[start_date:end_date,'KSM Returns'].std()*365**0.5 * 100}%"
    )
    print(
        f"The volatility of BTC/USD over the same period was {(1/(1+returns.loc[start_date:end_date,'inverse BTC Returns'])-1).std()*365**0.5*100}%"
    )
    print(
        f"The volatility of KSM/BTC over the same period was {ksm_btc.returns.loc[start_date:end_date,].values.std()*365**0.5*100}% \n"
    )
    end_date -= timedelta(config["analysis"]["historical_sample_period"])

#%%
# Based on the above comparison of LKSM and KSM, we're using KSM as a proxy for LKSM for
# the rest of this analysis, with the exception of the liquidity, for which we'll be using LKSM.
# Futhermore, the annual comparison showed that with the maturity of both, KSM and BTC, the volatility
# decreased and correlation increased. To better reflect this, we'll be using the past 1 year as sample.
#
# analysing the historic returns for USD/BTC, KSM/USD and KSM/BTC
for pair in [usd_btc, ksm_usd, ksm_btc]:
    pair.get_prices(
        start_date=(
            datetime.today() - timedelta(config["analysis"]["historical_sample_period"])
        ).strftime("%Y-%m-%d")
    )
    pair.calculate_returns()

    pair_ticker = f"{pair.base_token.ticker}/{pair.quote_token.ticker}"

    print(
        f"""The distribution of {pair_ticker} has:
            a kurtosis of {pair.returns.kurtosis()[0]}
            a skewness of {pair.returns.skew()[0]}
            and a mean of {pair.returns.mean()[0]}"""
    )
    pair.returns.plot.hist(bins=50, title=pair_ticker)

#%%
# Before computing the thresholds, we're looking at the liquidity
# The current TVL on Kintsugi is ~$1.75m USD locked in collateral.
# Starting with a 10% debt ceiling would mean to have a maximum of $175,000 worth of LKSM as collateral
# Assuming a worst case scenario where all LKSM is held by a single vault (or multiple vaults with similar liquidation price),
# would require a fire sale of the $175,000 LKSM. The most liquid swap would be into KSM and from there into other assets.
# This would incure an estimated slippage of ~3% which means that all thresholds need to be adjusted accordingly

liquidity_adjustment = 1 / (
    1 - 0.03
)  # slippage for trading $175,000 LSKM into KSM on Karura.
print(
    f"The estimated liquidity adjustment is ~{int(liquidity_adjustment * 100)}% of the debt value"
)

lksm_usd.returns.rename(columns={"Price": "LKSM_Returns"}, inplace=True)
ksm_usd.returns.rename(columns={"Price": "KSM_Returns"}, inplace=True)

cum_returns = (lksm_usd.returns + 1).join((ksm_usd.returns + 1)).cumprod().dropna()
lksm_depeg = max(abs(cum_returns.KSM_Returns - cum_returns.LKSM_Returns))

stETH_depeg = 0.07  # based on the max historic depeg of stETH vs ETH

depeg_risk_adjustment = 1 / (1 - max(lksm_depeg, stETH_depeg))
print(
    f"The estimated depeg risk adjustment is ~{int(depeg_risk_adjustment * 100)}% of the debt value"
)

total_risk_adjustment = depeg_risk_adjustment * liquidity_adjustment
print(
    f"The estimated total risk adjustment is ~{int(total_risk_adjustment * 100)}% of the debt value"
)
#%%
# BTC is the debt in the system and if BTC increases in price, the over-collateralization ratio drops
# Vice versa, if the price of KSM decreases, the collateralization ratio drops.
#
# To model this, we get the KSM/BTC price to have KSM as base currency (=collateral) and BTC as quote currency (=debt).
# We then select the n-th worst trajectorie of the price quotation.
#
# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 20,000 trajectories with a duration of 21
# and assume a normal distribution (GBM) with the mean of zero and std of the KSM/BTC ksm_btc over the past ~3 years
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
    "liquidation": {"analytical_threshold": None, "historical_threshold": None},
    "premium_redeem": {"analytical_threshold": None, "historical_threshold": None},
    "safe_mint": {"analytical_threshold": None, "historical_threshold": None},
}

for key, threshold in thresholds.items():
    threshold["analytical_threshold"] = (
        simple_analysis.get_threshold_multiplier(
            alpha=config["analysis"]["alpha"],
            at_step=config["analysis"]["thresholds"]["periods"][key],
        )
        * total_risk_adjustment
    )
    hist_var = ksm_btc.prices.pct_change(
        config["analysis"]["thresholds"]["periods"][key]
    ).dropna()
    hist_var = hist_var.sort_values("Price", ascending=False)
    threshold["historical_threshold"] = (
        1
        / (
            1
            + hist_var.iloc[
                int(len(hist_var) * config["analysis"]["alpha"]),
            ][0]
        )
        * total_risk_adjustment
    )

    print(
        f"The {key} threshold based on the analytical VaR for a confidence level of {config['analysis']['alpha']*100}% of KSM/BTC over {config['analysis']['thresholds']['periods'][key]} days is: {round(threshold['analytical_threshold'] *100,3)}%"
    )
    print(
        f"The {key} threshold based on the historic VaR for a confidence level of {config['analysis']['alpha']*100}% of KSM/BTC over {config['analysis']['thresholds']['periods'][key]} days is: {round(threshold['historical_threshold'] *100,3)}% \n"
    )

# %%
# Result: The VaR from the historic approach is higher than for the GBM simulation as expected in this case.
# The reason for this is that the montecarlo simulation more closely assambles a normal distribution, while the
# historic approach uses the historic returns which have over-kurtotis and is skewed to the right, hence
# extreme negative returns are more likely to occur. This also highlights some of the shortcomings of the approach for non-normal data.
# %%
