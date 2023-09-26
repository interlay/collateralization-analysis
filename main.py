# %%
import yaml
from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation
from datetime import datetime, timedelta
from helper.helper import round_up_to_nearest_5, get_total_risk_adjustment, print_banner
import logging
import sys

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

NETWORK = "polkadot"  # select between kusama and polkadot
DEBT = "btc"  # select usd for lending market and btc for vaults


ALPHA = config["analysis"]["alpha"]
PERIODS = config["analysis"]["thresholds"]["periods"]

debt_token = Token(config["debt"][DEBT], DEBT)
start_date = (
    datetime.today() - timedelta(config["analysis"]["historical_sample_period"])
).strftime("%Y-%m-%d")

logger = logging.getLogger()
logging.basicConfig(filename="analysis.log", level=logging.DEBUG)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.INFO)
logger.addHandler(consoleHandler)

print_banner()

logging.info(f"Date of the analysis: {datetime.today()}")
logging.info("====================================================================")
logging.info("Start running the collateral analysis with the following parameters:")
logging.info(
    f"""
    Debt currency:              {DEBT}
    Confidence level (alpha):   {ALPHA*100}%
    Number of path simulations: {config["analysis"]["n_simulations"]}
    Historical sample period:   {config["analysis"]["historical_sample_period"]}
    Threshold period in days:
        Safe Mint:              {PERIODS["liquidation"]}
        Premium Redeem:         {PERIODS["premium_redeem"]}
        Liquidations:           {PERIODS["safe_mint"]}
    """
)
logging.info("====================================================================")

for ticker, token in config["collateral"][NETWORK].items():
    logging.info(f"Start analysing {ticker}...")
    # BTC is the debt in the system and if BTC increases in price, the over-collateralization ratio drops
    # Vice versa, if the price of TOKEN decreases, the collateralization ratio drops.
    #
    # To model this, we get the TOKEN/BTC price to have TOKEN as base currency (=collateral) and BTC as quote currency (=debt).
    # We then select the n-th worst trajectorie of the price quotation.

    # If debt currency is the same as the token to be analysed, switch debt token.

    if ticker in ["usdt", "kbtc"]:
        debt_token = Token(
            "bitcoin" if ticker == "usdt" else "dollar",
            "btc" if ticker == "usdt" else "usd",
        )
    else:
        debt_token = Token(config["debt"][DEBT], DEBT)

    token_pair = Token_Pair(Token(token["name"], ticker), debt_token)
    token_pair.get_prices(start_date=start_date)

    # check if historic prices are available for the full sample period
    if (token_pair.prices.iloc[0, 0] == 0) or (
        token_pair.prices.index[0] - timedelta(1)
        > datetime.strptime(start_date, "%Y-%m-%d")
    ):
        logging.info(
            f"No sufficient historic prices for {ticker}/{token_pair.quote_token.ticker}"
        )

        # if not, use proxy to query prices
        proxy_ticker, proxy_name = next(iter(token.get("proxy").items()))
        token_pair = Token_Pair(Token(proxy_name, proxy_ticker), debt_token)
        logging.info(
            f"Trying to get prices for {proxy_ticker}/{token_pair.quote_token.ticker} as proxy pair"
        )
        token_pair.get_prices(start_date=start_date)

    try:
        token_pair.calculate_returns()
    except (KeyError, AttributeError) as e:
        logging.error(f"Failed to query prices for {ticker} and proxy {proxy_ticker}")
        pass

    # Initialize and run the simulation: Each path represents the price change of the collateral/debt
    # We simulate N trajectories with a duration of T days and daily steps
    # and assume a normal distribution (GBM) with the std of the pair over the past sample
    # period and a mean of 0.
    sim = Simulation(token_pair, strategy="GBM")
    sim.simulate(
        steps=1,
        maturity=PERIODS["liquidation"],
        n_simulations=config["analysis"]["n_simulations"],
        initial_value=1,
        sigma=token_pair.returns.std()[0],
        mu=0,
    )

    total_risk_adjustment = get_total_risk_adjustment(ticker, NETWORK, config)

    # Initialize the analysis
    simple_analysis = Analysis(sim)

    # This one is only used to store the Var to later compute the increments
    var = {
        "liquidation": {"analytical": None, "historical": None},
        "premium_redeem": {"analytical": None, "historical": None},
        "safe_mint": {"analytical": None, "historical": None},
    }

    # Get the VaR for each period using the historical and analytical
    # method.
    for key, value in var.items():
        value["analytical"] = (
            1
            / simple_analysis.get_threshold_multiplier(
                alpha=ALPHA,
                at_step=PERIODS[key],
            )
            * total_risk_adjustment
        )

        # create a rolling window of returns for the given window size(=PERIODS[key])
        hist_var = token_pair.prices.pct_change(PERIODS[key]).dropna()
        hist_var = hist_var.sort_values("Price", ascending=False)
        value["historical"] = (
            1
            + hist_var.iloc[
                int(len(hist_var) * ALPHA),
            ][0]
        ) * total_risk_adjustment

    # Quick and dirty, this computes the increments between the thresholds!
    # VaR (and hence thresholds) scale by the square root of time, so
    # 0-7 days VaR will be a larger increment than 7-14 days etc.
    # We want large increments between Safe_mint and premium_redeem
    # and need less safety margin between premium_redeem and liquidation.
    var_lists = {"analytical": [], "historical": []}
    increments = {"analytical": [], "historical": []}
    thresholds = {
        "liquidation": {"analytical": None, "historical": None},
        "premium_redeem": {"analytical": None, "historical": None},
        "safe_mint": {"analytical": None, "historical": None},
    }

    for method in var_lists.keys():
        for key in var.keys():
            var_lists[method].append(var[key][method])
    var_lists["analytical"].append(1)
    var_lists["historical"].append(1)

    for k in var_lists.keys():
        for i in range(len(var_lists[k]) - 1):
            increments[k].append(var_lists[k][i + 1] - var_lists[k][i])

    for i, key in enumerate(thresholds.keys()):
        thresholds[key]["analytical"] = 1 / (1 - sum(increments["analytical"][: i + 1]))
        thresholds[key]["historical"] = 1 / (1 - sum(increments["historical"][: i + 1]))

    for key, value in thresholds.items():
        rounded_threshold = round_up_to_nearest_5(
            max(thresholds[key]["analytical"], thresholds[key]["historical"]) * 100
        )

        logging.debug(
            f"The {key} threshold based on the analytical VaR for a confidence level of {ALPHA*100}% of {ticker}/{token_pair.quote_token.ticker} over {PERIODS[key]} days is: {round(thresholds[key]['analytical'] *100,3)}%"
        )
        logging.debug(
            f"The {key} threshold based on the historic VaR for a confidence level of {ALPHA*100}% of {ticker}/{token_pair.quote_token.ticker} over {PERIODS[key]} days is: {round(thresholds[key]['historical'] *100,3)}%"
        )
        logging.info(f"The suggested {key} threshold is {rounded_threshold}%")

# %%
