from importlib.resources import path
from data_request import Token_Pair
import QuantLib as ql
import numpy as np
from datetime import datetime
import pandas as pd


def parse_date_to_quantlib(date: pd.Timestamp) -> ql.Date:
    date = datetime.strftime(date,  "%d-%m-%Y")
    return ql.Date(*[int(i) for i in date.split("-")])


# TODO: Can this be generalized so that all processes can use this function for creating a path generator?
def path_generator(process, maturity, nSteps):
    dimensions = process.factors()
    times = ql.TimeGrid(maturity, nSteps)

    unifrom_sequence_generator = ql.UniformRandomSequenceGenerator(
        dimensions * nSteps, ql.UniformRandomGenerator())
    gaussian_sequence_generator = ql.GaussianRandomSequenceGenerator(
        unifrom_sequence_generator)
    path_generator = ql.GaussianMultiPathGenerator(
        process, list(times), gaussian_sequence_generator, False)

    return path_generator


class Simulation():
    def __init__(self, token_pair: Token_Pair, strategy: str) -> None:
        self._token_pair = token_pair
        self._strategy = strategy

    @property
    def strategy(self) -> str:
        return self._strategy

    @property
    def token_pair(self) -> Token_Pair:
        return self._token_pair

    def black_process(self):
        riskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(
            self._params["start_date"], 0.05, ql.Actual365Fixed()))
        volTS = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(
            self._params["start_date"], ql.NullCalendar(), self._params["sigma"], ql.Actual365Fixed()))
        return ql.BlackProcess(self._params["initial_value"], riskFreeTS, volTS)

    def geometric_brownian_motion(self) -> ql.GeometricBrownianMotionProcess:
        return ql.GeometricBrownianMotionProcess(
            # I dont understand why this fails without .value()
            self._params["initial_value"].value(), self._params["mu"], self._params["sigma"])

    def heston_process(self) -> ql.Merton76Process:
        riskFreeTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"], 0.05, ql.Actual365Fixed()))
        dividendTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"], 0.01, ql.Actual365Fixed()))

        v0, kappa, theta, rho, sigma = 0.005, 0.8, 0.008, 0.2, self._params["sigma"]
        return ql.HestonProcess(riskFreeTS, dividendTS, self._params["initial_value"], v0, kappa, theta, sigma, rho)

    def merton_jump_diffusion(self) -> ql.Merton76Process:
        dividendTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"], 0.02, ql.Actual365Fixed()))
        riskFreeTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"], 0.01, ql.Actual365Fixed()))
        volTS = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(
            self._params["start_date"], ql.NullCalendar(), self._params["sigma"], ql.Actual365Fixed()))

        jumpIntensity = ql.QuoteHandle(ql.SimpleQuote(1.0))
        jumpVolatility = ql.QuoteHandle(ql.SimpleQuote(
            self._params["sigma"] * np.sqrt(0.25 / jumpIntensity.value())))
        meanLogJump = ql.QuoteHandle(
            ql.SimpleQuote(-jumpVolatility.value()*jumpVolatility.value()))

        return ql.Merton76Process(self._params["initial_value"], dividendTS, riskFreeTS, volTS, jumpIntensity, meanLogJump, jumpVolatility)

    def simulate(self, steps: int = 365, maturity: int = 1, n_simulations: int = 50, type="returns", **kwargs) -> None:
        """
        Given the time unit is days, the default arguments represent a path with a length of 1 year, consisting of 365 days. 
        1000 of those paths will be simulated.

        Args:
            steps (int, optional): Steps within a period of the maturity. Defaults to 365, which could be a year if the time unit is days.
            maturity (int, optional): Maturity periods determining the length of the simulation. Defaults to 1.
            n_simulations (int, optional): _description_. Defaults to 1000.
        """

        # TODO: Make some of them arguments in the simulate function
        self._params = {
            "sigma": self.token_pair.returns.std()[0],
            "mu": 0,
            "initial_value": ql.QuoteHandle(ql.SimpleQuote(self.token_pair.prices.iloc[0][0])),
            "start_date": parse_date_to_quantlib(self.token_pair.prices.index[0]),
            "total_steps": int(maturity * steps),
            "_paths": []
        }

        # TODO: Refactor this to allow more flexibility
        if self.strategy == "GBM":
            process = self.geometric_brownian_motion()

            # TODO: should this be refactored? If so, how?
            for step in range(n_simulations):
                _path_generator = path_generator(
                    process, maturity, self._params["total_steps"])
                path = _path_generator.next().value()
                self._params["_paths"].append([path[0][i]
                                               for i in range(self._params["total_steps"] + 1)])

            # TODO: Should this rather be stored in token_pair to make it easier to use with the analysis package?
            self.paths = pd.DataFrame(self._params["_paths"]).transpose()

        elif self.strategy == "merton_jump_diffusion":
            process = self.merton_jump_diffusion()

            for step in range(n_simulations):
                # path generator can be taken out of this loop, same above, maybe this can be refactured further...
                _path_generator = path_generator(
                    process, maturity, self._params["total_steps"])
                print("Hallo")
                path = _path_generator.next().value()
                self._params["_paths"].append([path[0][i]
                                               for i in range(self._params["total_steps"] + 1)])

            # TODO: Should this rather be stored in token_pair to make it easier to use with the analysis package?
            self.paths = pd.DataFrame(self._params["_paths"]).transpose()

        elif self.strategy == "heston_process":
            process = self.heston_process()

            for step in range(n_simulations):
                # path generator can be taken out of this loop, same above, maybe this can be refactured further...
                _path_generator = path_generator(
                    process, maturity, self._params["total_steps"])
                path = _path_generator.next().value()
                self._params["_paths"].append([path[0][i]
                                               for i in range(self._params["total_steps"] + 1)])

            # TODO: Should this rather be stored in token_pair to make it easier to use with the analysis package?
            self.paths = pd.DataFrame(self._params["_paths"]).transpose()

        elif self.strategy == "black_process":
            process = self.black_process()

            for step in range(n_simulations):
                # path generator can be taken out of this loop, same above, maybe this can be refactured further...
                _path_generator = path_generator(
                    process, maturity, self._params["total_steps"])
                path = _path_generator.next().value()
                self._params["_paths"].append([path[0][i]
                                               for i in range(self._params["total_steps"] + 1)])

            # TODO: Should this rather be stored in token_pair to make it easier to use with the analysis package?
            self.paths = pd.DataFrame(self._params["_paths"]).transpose()
