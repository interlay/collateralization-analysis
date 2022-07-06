from matplotlib import pyplot as plt
from data.data_request import Token_Pair
from data.market import Automted_Market_Maker
from simulation.simulation import Simulation


class Analysis:
    def __init__(self, simulation: Simulation):
        self._simulation = simulation

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

    def get_liquidation_threshold(self, amm_debt: Automted_Market_Maker, amm_collatera: Automted_Market_Maker,
                                  debt_outstanding: int, profitability_threshold: float):
        # It's assumed that the start of the strajectory is the unknown threshold x that has been reached at day 0.
        # From now on, arbitrageurs will buy iBTC and burn it in exchange for collateral.
        for _, path in self._simulation.paths.iteritems():
            for row in path.iterrows():

                amm.set_exchange_rate

                """
                
                """
