import math


def round_up_to_nearest_5(num: float) -> int:
    """Rounds up number to the nearest 5

    Args:
        num (float): Number to round up

    Returns:
        int: Rounded number
    """
    return math.ceil(num / 5) * 5


def get_total_risk_adjustment(ticker: str, network: str, config: dict()) -> float:
    """Reads risk adjustments from config and multiplies all of them to
    return a single 'total risk adjustment' which is used to increase the
    thresholds for risks that are not captured with the simulation.

    E.g:
     - Liqudity risk (=slippage)
     - Depeg risk (=max historic depeg)


    Args:
        ticker (str): Ticker of the token
        config (dict): Imported config used for the analysis

    Returns:
        float: A single multiplier used to adjust (increase) the thresholds.
    """
    token = config["collateral"][network].get(ticker)
    if token.get("risk_adjustment").get("liquidity_adjustment"):
        liquidity_adjustment = token.get("risk_adjustment").get("liquidity_adjustment")
    else:
        liquidity_adjustment = 0

    liquidity_adjustment_multiplier = 1 / (
        1 - liquidity_adjustment
    )  # slippage for trading

    if token.get("risk_adjustment").get("depeg_adjustment"):
        depeg_adjustment = token.get("risk_adjustment").get("depeg_adjustment")
    else:
        depeg_adjustment = 0

    depeg_adjustment_multiplier = 1 / (
        1 - depeg_adjustment
    )  # adjustment for depegging event

    return liquidity_adjustment_multiplier * depeg_adjustment_multiplier
