# Vault Collateralization Analysis

This package contains a framework for conducting risk analysis of collateral for vaults and is split into three different parts.

1. Data
2. Simulation
3. Analysis

# Data
This part contains classes that represent token and token pairs as well as a class for requesting price data for the token.

## Usage:
This example creates two tokens, one represeting the bitcoin, the other fiat USD and then creates a token pair.
Then it sends a price request to coingecko (default parameter) and calculates daily returns (default parameter).

'''
from data.data_request import Token, Token_Pair

quote_currency = Token("usd", "USD")
base_currency = Token("bitcoin", "BTC")

pair = Token_Pair(base_currency, quote_currency)
pair.get_prices()
pair.calculate_returns()
'''

Furthermore, it contains a class which simulates an automated market maker (AMM). This will serve to simulate the slippage for a given token pair, based on the TVL of the pool.

## Usage:
'''
start_price = prices.iloc[0, 0] # the price at which you want to initialize the AMM. Here it's the start price of bitcoin of the given price history
TVL = 10_000_000 # size of the pool in quote_token units. so here it is USD
amm = Automted_Market_Maker(
    pair.base_token,
    pair.quote_token,
    base_token_amount=TVL / 2 / start_price, # half of the TVL is allocated to bitcoin (USD_value / bitcoin price)
    quote_token_amount=TVL / 2, # the other half is allocated to the quote_token. remember, TVL is denominated in quote_token
)
'''

# Simulation
This part contains a class that instantiates a random number generator based on a given random process, passed as parameters to the constructor.
The number generator, in conjunction with the random process, generates 'n' (=10,000) random paths for the given token pair.
The maturity parameter determines the length of the path, while the steps determine the intervall per period (e.g. 3 periods * 365 steps). In this example, this will generate paths consisting of 3 years, each containing 365 days, since we pass daily data into the object.



## Usage:
'''
sim = Simulation(pair, strategy="GBM")
sim.simulate(steps=365, maturity=3, n_simulations=10000)
'''

# Analysis
This package imports the analysis class, which will use the results of the simulation and conduct analysis upon it.
TODO: Add example usage.


# Threshold analysis
TODO: Add an example for a collateral analysis.


The analysed parameters are LIQUIDATION_THRESHOLD and SECURE_THRESHOLD. The bridge also uses a PREMIUM_REDEEM_THRESHOLD to increase system security, but premium redeems are assumed not to occur in order to better capture tail risk.

Vaults are modelled as a single entity that mints the maximum wrapped amount on the first simulated day, at the secure threshold.

One step of the simulation generates multiple price trajectories for both the collateral and wrapped asset, considering their observed correlation. Then, the "worst" trajectory of the collateral asset is picked: where collateral price is lowest with respect to the wrapped aspect on the final day.

If, on any day, vaults fall below the liquidation ratio, their entire collateral is seized by the liquidation vault, causing the 1:1 peg to be destabilised. At this point, the "debt" in the system can only be liquidated by arbitrageurs who burn wrapped tokens in exchange for collateral at a beneficial rate. How beneficial this rate is, is initially decided by the liquidation threshold; but if the backing asset keeps decreasing in value arbitrage profits can reach zero. In the event that the liquidation vault becomes undercollateralized, the relative value of the wrapped tokens to BTC would be equal to the collateralization rate.

Another conservative assumption is that liquidators start minting wrapped tokens only after the peg is destabilized, thus requiring liquidity in both collateral and BTC. The larger the debt ceiling in the bridge, the more likely it is that liquidiators would move the market. An AMM with the current liquidity capacity is used to model the slippage of the trades. 


Future improvements:
- Model liquidation behaviour for premium redeem.
- When more kBTC liquidity becomes available, relax assumptions about burn redeem behaviour. # Comment, why is that?
- Replace the Gaussian Brownian Motion model with one that considers clustered volatility.
- Aggregate trading data from multiple centralized exchanges.
- Use a loss function that priotizes outliers when training the slippage model.
- In a similar work, Gauntlet (https://medium.com/gauntlet-networks/karura-parameter-recommendation-methodology-6ce7fe06cb77) also train a price impact model to measure how quickly the market recovers after large trades. Such a model should be added to this framework too.
