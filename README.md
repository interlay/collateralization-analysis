# Vault Collateralization Analysis

This work analyzes historic data of KSM, DOT, KINT, USDC and BTC in order to decide on security parameters for the Kintsugi bridge. For assets traded in order-book exchanges, the code is general enough such that inspecting a new collateral asset can be done with minimal effort.

Historic price data is gathered from Coingecko, while order book data is collected from the Binance API. Binance is preferred over the other centralized exchanges because it has by far the largest trading volume (https://coinmarketcap.com/rankings/exchanges/).

The approach from Gudgeon et al's DeFi Crisis paper (https://arxiv.org/pdf/2002.08099.pdf) is applied, which models price trajectories as stochastic processes. In addition, a simple slippage model is used as part of the burn redeem simulation.

The analysed parameters are LIQUIDATION_THRESHOLD and SECURE_THRESHOLD. The bridge also uses a PREMIUM_REDEEM_THRESHOLD to increase system security, but premium redeems are assumed not to occur in order to better capture tail risk.

Vaults are modelled as a single entity that mints the maximum wrapped amount on the first simulated day, at the secure threshold.

One step of the simulation generates multiple price trajectories for both the collateral and wrapped asset, considering their observed correlation. Then, the "worst" trajectory of the collateral asset is picked: where collateral price is lowest with respect to the wrapped aspect on the final day.

If, on any day, vaults fall below the liquidation ratio, their entire collateral is seized by the liquidation vault, causing the 1:1 peg to be destabilised. At this point, the "debt" in the system can only be liquidated by arbitrageurs who burn wrapped tokens in exchange for collateral at a beneficial rate. How beneficial this rate is, is initially decided by the liquidation threshold; but if the backing asset keeps decreasing in value arbitrage profits can reach zero. In the event that the liquidation vault becomes undercollateralized, the relative value of the wrapped tokens to BTC would be equal to the collateralization rate.

Another conservative assumption is that liquidators start minting wrapped tokens only after the peg is destabilized, thus requiring liquidity in both collateral and BTC. Although Gudgeon et al's paper assumes liquidity is equal to the daily traded volume, this works takes the more thorough approach of training a transaction cost (slippage) model. The larger the debt ceiling in the bridge, the more likely it is that liquidiators would move the market. For invidividual KSM trades, which achieve small volumes compared to DOT, there is close to zero correlation between buy order amount (buyer-is-taker) and price movement. However, correlation can be noticed when consecutive buy order are considered (with no sells in-between). After some manual filtering, the slippage model is trained on the most extreme of these data points.


Future improvements:
- Model liquidation behaviour for premium redeem.
- When more kBTC liquidity becomes available, relax assumptions about burn redeem behaviour.
- Replace the Gaussian Brownian Motion model with one that considers clustered volatility.
- The definition of "worst" price trajectory can be improved in the future by focusing on sharp price drops.
- Aggregate trading data from multiple centralized exchanges.
- Use a loss function that priotizes outliers when training the slippage model.
- In a similar work, Gauntlet (https://medium.com/gauntlet-networks/karura-parameter-recommendation-methodology-6ce7fe06cb77) also train a price impact model to measure how quickly the market recovers after large trades. Such a model should be added to this framework too.
