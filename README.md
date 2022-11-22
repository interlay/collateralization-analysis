# Vault Collateralization Analysis

This repo containts a package for analyzing collateral as well as the python files containing the implementation for specific collaterals. The repo also contains a `main.py` file which will iterate over all implemented tokens and print the results in stdout and `analysis.log`.

# Setup

Optional: Install pipenv to create a virtual environment for this project
Requirement: Have python >3.8 installed. Otherwise install it:

```
sudo apt-get update
sudo apt-get install python3.8
```

```
pip install --user pipenv
```

To install the depencies for this project and enter the virtual environment:

```
pipenv install
pipenv shell
```

To run all of the implemented analysis using python:

```
python main.py
```
this will print the results in stdout and create a more detailed log of the results and parameters used in the `analysis.log` file.


or to run any of the analysis in particular using python

```
cd results/btc_<col>
python <analysis_file.py>
```

To run any unit tests

```
pytest test_data_request.py
```

Or just run any of the notebooks inside your IDE or a web based jupyter environment.

# Implementation
## Files
The `main.py` file can be found in the root directory and run as is.


The individual files can be found under `/results/<token_pair>`. The current implementations of the analysis include:

1. aUSD
2. DOT
3. KSM
4. LKSM
5. stKSM
6. USDT

Each python file contains a detailed description of the anlysis process and can be run as is.
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
collateral:
  dot: # coingecko ticker of the token to be analyzed
    name: "polkadot" # coingecko API id of that token
    risk_adjustment:
      liquidity_adjustment: # optional: slippage as decimal for the trade of given size
      depeg_adjustment: # optional: e.g. max historic depeg of that asset or comparable asset
```

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

This package imports the analysis class, which will use the results of the simulation and conduct analysis upon it.
TODO: Add example usage.

# Threshold analysis

An example of an analysis for the token pair BTC/KSM can be found in `results/btc_ksm/btc_ksm_analysis.py`.

The analysed parameters are `liquidation_threshold`, `premium_redeem_threshold` and `secure_threshold`. The bridge also uses a `premium_redeem_threshold` to increase system security, but premium redeems are assumed not to occur in order to better capture tail risk.

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

Future improvements:

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
