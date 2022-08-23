from matplotlib import pyplot as plt
from data.data_request import Token_Pair
from data.market import Automted_Market_Maker
from simulation.simulation import Simulation
import pandas as pd


def get_initial_drawdown(series: pd.Series) -> float:
    """Computes the maximum drawdown from the first data point in the series.

    Args:
        series (pd.Series): A time series object containing price return data.

    Returns:
        float: The highest drawdown from the first data point in the series
    """
    return (min(series) / series[0] - 1)


class Analysis:
    """This class implements methods to analyse the results of a given simulation
    """

    def __init__(self, simulation: Simulation):
        self._simulation = simulation

    @property
    def simulation(self) -> Simulation:
        return self._simulation

    # TODO: Refactor this, maybe even into a separate class for plots.
    def plot_returns(self, data_label, title, type="hist"):
        if type == "hist":
            plt.hist(
                self._simulation.token_pair.returns,
                density=True,
                bins=30,
                alpha=0.5,
                label=data_label,
            )
            plt.ylabel("Occurences")
            plt.xlabel("Percentage change")
            plt.legend(loc="upper right")
            plt.title(title)

        elif type == "line":
            length = len(self._simulation._params["_paths"])
            f, subPlots = plt.subplots(sharex=True)
            plt.rcParams["figure.figsize"] = [16.0, 10.0]
            f.suptitle("Path simulations n=" + str(length))
            subPlots.set_title(str(self._simulation.strategy))

            for _, path in self._simulation.paths.iteritems():
                subPlots.plot(path)

    def get_threshold_multiplier(self, alpha: float, at_step: int = None) -> float:
        """Estimates the premium multiplier for the threshold by getting the initial maxmimum drawdown of the i-th interval corrosponding to the given alpha.
        Example: alpha=0.99 means that the functions selects the maximum drawdown that corrosponds to the 99th-percentile/interval.

        Args:
            alpha (float): Confidence interval.
            at_step (int): default None. If None, the whole time series is used for the estimation. If a step is given, the path is truncated up to that step.

        Returns:
            float: Returns the threshold multiplier
        """
        
        at_step = -1 if at_step is None else at_step
        
        if at_step > len(self._simulation.paths[0]):
            raise Exception("Step must be smaller or equal to the length of the path.")
        
        initial_drawdowns = []
        for _, path in self._simulation.paths.iteritems():
            initial_drawdowns.append(get_initial_drawdown(path[:at_step]))

        # These drawdowns are being represented as negative percentage returns
        # Sorting this in reverse order (descending) mean that the 99th percentile
        # is the 99th percent lowest return
        initial_drawdowns.sort(reverse=True)
        
        # This is the value at risk (VaR) at a given confidence interval (=alpha)
        # In this case, the VaR is represented as a negative number as it is the 
        # n_th worst 'initial' drawdown of the simulation
        value_at_risk = initial_drawdowns[int(len(initial_drawdowns) * alpha)]
        
        # Inverting this then gives us the threshold that 
        return (1 / (1 + value_at_risk))

    def get_liquidation_threshold(self, TVL: int,
                                  debt_outstanding: int):
        """Experimental WIP"""
        # It's assumed that the start of the strajectory is the unknown threshold x that has been reached at day 0.
        # From now on, arbitrageurs will buy iBTC and burn it in exchange for collateral.
        for _, path in self._simulation.paths.iteritems():
            for _, value in path.iteritems():

                # would be better to calculate the price change from yesterday to today and pass this as the exact slippage parameter for a swap
                # to align the AMM back to market prices instead of instantiating it new everytime which is also imprecise I think.
                amm = Automted_Market_Maker(
                    self.simulation.token_pair.base_token,
                    self.simulation.token_pair.quote_token,
                    base_token_amount=TVL / 2 / value,
                    quote_token_amount=TVL / 2,
                )

                """
                
                """
