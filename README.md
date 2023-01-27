# Vault Collateralization Analysis

This repo containts a package for analyzing collateral as well as the python files containing the implementation for specific collaterals. The repo also contains a `main.py` file which will iterate over all implemented tokens and print the results in stdout and `analysis.log`.

# Setup

Optional: Install pipenv to create a virtual environment for this project <br>
Requirement: Have python >3.8 installed. Otherwise install it using (Ubuntu Linux):

```
sudo apt-get update
sudo apt-get install python3.8
```

For other Linux distributions please look at this [guide](https://docs.python-guide.org/starting/install3/linux/).

```
pip install --user pipenv
```

Clone the repo and change into its root directory:
```
git clone https://github.com/interlay/collateralization-analysis.git && cd collateralization-analysis
```


To install the depencies for this project and enter the virtual environment:

```
pipenv install
pipenv shell
```

To run all of the implemented analysis:

```
python main.py
```
This will print the results in stdout and create a more detailed `analysis.log` file with the results and parameters used in the simulation.


To run any of the analysis in particular:

```
cd results/btc_<col>
python <analysis_file.py>
```

To run any unit tests

```
pytest test_data_request.py
```
TODO: Fix the unit tests. The unit tests still fail due to implementation error.

# Implementation
## Files
The individual files can be found under `/results/<token_pair>`.

The `main.py` file can be found in the root directory and run as is.
Current implementations in `main.py` include:

**Polkadot**
1. aUSD
2. DOT
3. USDT
4. GLMR
5. LDOT
6. stDOT
7. ASTR

**Kusama**
1. kBTC
2. KSM
3. LKSM
4. stKSM
5. sKSM
6. MOVR
7. USDT
8. aUSD
9. vKSM

Note, that the results can vary slightly depending on the date the code is run, since there is no fixed end date set in the code, as well as due to the fact that the estimates are the result of a simulation with an underlying random process.

## Config
The `config.yaml` determines the parameters of the simulation and analysis as well as which tokens will be analysed by `main.py`. 

```
analysis:
  alpha: 0.99 # == 99% confidence level
  n_simulations: 20_000 # number of simulations
  historical_sample_period: 365 #sample period in days from which standard deviation is estimated
  thresholds:
    periods: # length for each threshold simulation in days
      liquidation: 7
      premium_redeem: 14
      safe_mint: 21
debt:
  btc: "bitcoin" # BTC is used for estimations for the bridge
  usd: "dollar" # USD is used for the lending protocol since most tokens will be collateralized or borrowed against USD
collateral:
  polkadot:
    dot: # coingecko ticker of the token to be analyzed
      name: "polkadot" # coingecko API id of that token
      risk_adjustment:
        liquidity_adjustment: # optional: slippage as decimal for the trade of given size
        depeg_adjustment: # optional: e.g. max historic depeg of that asset or comparable asset
```

In `main.py` you can determine the `NETWORK` (Polkadot or Kusama) for which you want to run the analysis as well as the `DEBT`currency (Bitcoin or USD).

# Package

The package contains a framework for conducting risk analysis of collateral for vaults and is split into three different parts.

1. Data
2. Simulation
3. Analysis

## Data

This part contains classes that represent token and token pairs as well as a class for requesting price data for the token.

### Usage:

This example creates two tokens, one represeting the bitcoin, the other fiat USD and then creates a token pair.
Then it sends a price request to coingecko (default parameter) and calculates daily returns (default parameter).

```
from data.data_request import Token, Token_Pair

quote_currency = Token("usd", "USD")
base_currency = Token("bitcoin", ")

pair = Token_Pair(base_currency, quote_currency)
pair.get_prices()
pair.calculate_returns()
```

## Simulation

This part contains a class that instantiates a random number generator based on a given random process, passed as parameters to the constructor.
The number generator, in conjunction with the random process, generates 'n' (=20,000) random paths for the given token pair.
The maturity parameter determines the length of the path, while the steps determine the intervall per period (e.g. 30 periods \* 24 steps). In this example, this will generate paths consisting of 30 days, each containing 24 steps representing the hours per day. The standard behaviour, if no parameters are passed for mean and sigma is to estimate those values based on the given sample. Since our sample consists of daily data, this is consistent. If the maturity would represent years and the steps days, we would need to adjust the mean and sigma accordingly.

### Usage:

```
sim = Simulation(pair, strategy="GBM")
sim.simulate(steps=24, maturity=30, n_simulations=10_000)
```

## Analysis

This package imports the analysis class, which will use the results of the simulation and conduct analysis upon it. <br>
### Usage

```
simple_analysis = Analysis(sim)
simple_analysis.get_threshold_multiplier(
            # any confidence level you want to use for estimation
            alpha=0.99,

            # number of periods (days) within which the threshold should not be breached
            at_step=7, 
        )
    )
```

# Threshold analysis
## Interpretation of Results
Given the parameters of the `config.yaml`, the thresholds can be interpreted in a way that, starting at a thresholds collateral-debt-ratio, this ratio will not drop below 100% (break the peg) within the defined period (e.g. 21 days), with a probability of 'alpha' (e.g. 99%).

If the analysis is supposed to be used for the lending market, the inverse of the reported thresholds needs to be taken (and rounded) to arrive at the loan-to-value ratio. In the lending protocol the threshold for the premium redeem serves as the maximum borrowing threshold, since there is no premium redeem.


## Process
The analysed parameters are `liquidation_threshold`, `premium_redeem_threshold` and `secure_threshold`. The bridge also uses a `premium_redeem_threshold` to increase system security, but premium redeems are assumed not to occur in order to better capture tail risk.

The analysis applies a value at risk (VaR) approach for a given confidence level and a given duration. The confidence level is the same for all thresholds, only the time frame changes. Given that the ultimate goal is to prevent a depeg event, the analysis assumes a 1:1 peg and scales this ratio by the inverse of the VaR for each threshold. E.g:

```
Liquidation_Threshold = 1 / (1 - VaR(7days, 99%)) 
Premium_Redeem_Threshold = 1 / (1 - VaR(14days, 99%))
Safe_Mint_Threshold = 1 / (1 - VaR(21days, 99%))
```

All thresholds are then adjusted for the liquidity risk and depeg risk (event risk). The liquidity risk adjustment takes into account the slippage that would occure, if the total supply (=supply_cap, locked as collateral) would have to be liquidated in a single transaction and swaped against another token in the most liquid pool available. The depeg risk adjust the threshold for the most severe depeg of the tokens history. If no depeg occured so far, a comparable depeg of a proxy token is used instead. This is done because such event risk cannot be captured adequately by the standard deviation or might not have occured within the sample period. 

Although this does not guarantee that the peg never breaks, it sets a conservative estimate, taking into account the cost of capital for vaults.
To apply a conservative approach for the VaR estimation, this model choses the higher VaR of the historical and analytical (simulation) approach to account for non-normal distributions.

<b>The analysis makes the following assumptions: </b>

1. Liquidators might need up to 7 trading days to close out all under-collateralized iBTC positions
2. Liquidators would have 7 days time to increase the collateral ratio above the premium redeem threshold again before actual liquidations happen. Though, we assume that no premium redeems happen, to be more conservative.
3. Vault operators check their collateralization ratio at least once every 14 days
4. Liquidators settle their trade in a stable coin position. That mean that if the collateral is a not a stable coin, they will want to swap it for a stable coin.

<b>The simulation makes the following assumptions: </b>

1. The standard deviation is constant and equal to the historic standard deviation.
2. The short term mean is assumed to be zero. This is because the estimation of the mean is very unstable and does usually only hold in the long run, if at all.
3. The distrubution of returns follows a normal distribution (due to general brownian motion model, but can be relaxed).

Vaults are modelled as a single entity that mints the maximum wrapped amount on the first simulated day, at the secure threshold.

If, on any day, vaults fall below the liquidation ratio, their entire collateral is seized by the liquidation vault, causing the 1:1 peg to be destabilised. At this point, the "debt" in the system can only be liquidated by arbitrageurs who burn wrapped tokens in exchange for collateral at a beneficial rate. How beneficial this rate is, is initially decided by the liquidation threshold; but if the backing asset keeps decreasing in value arbitrage profits can reach zero. In the event that the liquidation vault becomes undercollateralized, the relative value of the wrapped tokens to would be equal to the collateralization rate.

The larger the debt ceiling in the bridge, the more likely it is that liquidiators would move the market. An AMM with the current liquidity capacity shall be used to model the slippage of the trades in the future. For now, we rely on the slippage information of existing pools.


## Future improvements:

- Model liquidation behaviour for premium redeem.
- Replace the Gaussian Brownian Motion model with one that considers clustered volatility.
- Aggregate trading data from multiple centralized exchanges.
- Use a loss function that priotizes outliers when training the slippage model.
- In a similar work, Gauntlet (https://medium.com/gauntlet-networks/karura-parameter-recommendation-methodology-6ce7fe06cb77) also train a price impact model to measure how quickly the market recovers after large trades. Such a model should be added to this framework too.

## Details

### Liquidation Process

Liquidation process: 1. Off-chain worker trigger liquidation and vault seizes collateral 2. A third party can now burn iBTC to receive the collateral
2.1 Buy iBTC
2.2 Burn iBTC
2.3 Receive collateral 3. (Optional) Swap collateral into other currency
