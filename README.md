# Vault Collateralization Analysis
This repo containts a package for analyzing collateral as well as the jupyter notebooks containing the implementation for specific collaterals.

# Notebooks
The current implementations of the analysis include:
1. BTC/aUSD: btc_ausd_analysis.ipynb

Each notebook contains a detailed description of the anlysis process and can be run as is.
Note, that the results can vary slightly depending on the date the code is run, since there is no fixed end date set in the code, as well as due to the fact that the estimates are the result of a simulation with an underlying random process.


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
base_currency = Token("bitcoin", "BTC")

pair = Token_Pair(base_currency, quote_currency)
pair.get_prices()
pair.calculate_returns()
```

Furthermore, it contains a class which simulates an automated market maker (AMM). This will serve to simulate the slippage for a given token pair, based on the TVL of the pool.

### Usage:
```
start_price = prices.iloc[0, 0] # the price at which you want to initialize the AMM. Here it's the start price of bitcoin of the given price history
TVL = 10_000_000 # size of the pool in quote_token units. so here it is USD
amm = Automted_Market_Maker(
    pair.base_token,
    pair.quote_token,
    base_token_amount=TVL / 2 / start_price, # half of the TVL is allocated to bitcoin (USD_value / bitcoin price)
    quote_token_amount=TVL / 2, # the other half is allocated to the quote_token. remember, TVL is denominated in quote_token
)
```

## Simulation
This part contains a class that instantiates a random number generator based on a given random process, passed as parameters to the constructor.
The number generator, in conjunction with the random process, generates 'n' (=10,000) random paths for the given token pair.
The maturity parameter determines the length of the path, while the steps determine the intervall per period (e.g. 30 periods * 24 steps). In this example, this will generate paths consisting of 30 days, each containing 24 steps representing the hours per day. The standard behaviour, if no parameters are passed for mean and sigma is to estimate those values based on the given sample. Since our sample consists of daily data, this is consistent. If the maturity would represent years and the steps days, we would need to adjust the mean and sigma accordingly.



### Usage:
```
sim = Simulation(pair, strategy="GBM")
sim.simulate(steps=24, maturity=30, n_simulations=10000)
```

## Analysis
This package imports the analysis class, which will use the results of the simulation and conduct analysis upon it.
TODO: Add example usage.


# Threshold analysis
An example of an analysis for the token pair BTC/aUSD can be found in `btc_ausd_analysis.ipynb`.

The analysed parameters are `liquidation_threshold` and `secure_threshold`. The bridge also uses a `premium_redeem_threshold` to increase system security, but premium redeems are assumed not to occur in order to better capture tail risk.

<b>The analysis makes the following assumptions: </b>
1. Liquidators might need up to 7 trading days to close out all under-collateralized iBTC positions
2. Vault operators check their collateralization ratio at least once every 14 days and might need up to 7 days to top up their collateral (=21 days in total)
3. There is enough liquidity to buy bitcoin and (self-)mint to burn it to redeem the collateral
4. Liquidators settle their trade in a stable coin position. That mean that if the collateral is a not a stable coin, they will want to swap it for a stable coin.

Vaults are modelled as a single entity that mints the maximum wrapped amount on the first simulated day, at the secure threshold.

If, on any day, vaults fall below the liquidation ratio, their entire collateral is seized by the liquidation vault, causing the 1:1 peg to be destabilised. At this point, the "debt" in the system can only be liquidated by arbitrageurs who burn wrapped tokens in exchange for collateral at a beneficial rate. How beneficial this rate is, is initially decided by the liquidation threshold; but if the backing asset keeps decreasing in value arbitrage profits can reach zero. In the event that the liquidation vault becomes undercollateralized, the relative value of the wrapped tokens to BTC would be equal to the collateralization rate.

The larger the debt ceiling in the bridge, the more likely it is that liquidiators would move the market. An AMM with the current liquidity capacity shall be used to model the slippage of the trades in the future. 


Future improvements:
- Model liquidation behaviour for premium redeem.
- When more kBTC liquidity becomes available, relax assumptions about burn redeem behaviour. # Comment, why is that?
- Replace the Gaussian Brownian Motion model with one that considers clustered volatility.
- Aggregate trading data from multiple centralized exchanges.
- Use a loss function that priotizes outliers when training the slippage model.
- In a similar work, Gauntlet (https://medium.com/gauntlet-networks/karura-parameter-recommendation-methodology-6ce7fe06cb77) also train a price impact model to measure how quickly the market recovers after large trades. Such a model should be added to this framework too.


## Details
### Liquidation Process

Liquidation process:
    1. Off-chain worker trigger liquidation and vault seizes collateral
    2. A third party can now burn iBTC to receive the collateral
        2.1 Buy iBTC
        2.2 Burn iBTC
        2.3 Receive collateral
    3. (Optional) Swap collateral into other currency