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
    if isinstance(process, ql.GeometricBrownianMotionProcess):
        generator = ql.UniformRandomGenerator()
        sequenceGenerator = ql.UniformRandomSequenceGenerator(
            nSteps, generator)
        gaussianSequenceGenerator = ql.GaussianRandomSequenceGenerator(
            sequenceGenerator)
        path_generator = ql.GaussianPathGenerator(
            process, maturity, nSteps, gaussianSequenceGenerator, False)

    elif isinstance(process, ql.Merton76Process):
        generator = ql.UniformRandomGenerator()
        sequenceGenerator = ql.UniformRandomSequenceGenerator(
            nSteps, generator)
        rng = ql.UniformRandomSequenceGenerator(ql.UniformRandomGenerator())
        sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
        pathGenerator = ql.GaussianMultiPathGenerator(
            process, sequenceGenerator, False)

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

    def geometric_brownian_motion(self, **kwargs) -> ql.GeometricBrownianMotionProcess:
        return ql.GeometricBrownianMotionProcess(
            # fails for some reason due to the initial value type mismatch
            self._params["initial_value"], self._params["mu"], self._params["sigma"])

    def merton_jump_diffusion(self) -> ql.Merton76Process:
        dividendTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"], 0.01, ql.Actual365Fixed()))

        riskFreeTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"], 0.01, ql.Actual365Fixed()))
        volTS = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(
            self._params["start_date"], ql.NullCalendar(), self._params["sigma"], ql.Actual365Fixed()))
        process = ql.BlackProcess(
            self._params["initial_value"], riskFreeTS, volTS)

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
        if self.strategy == "GMB":
            process = self.geometric_brownian_motion()

            # TODO: should this be refactored? If so, how?
            for step in range(n_simulations):
                _path_generator = path_generator(
                    process, maturity, self._params["total_steps"])
                path = _path_generator.next().value()
                self._params["_paths"].append([path[i]
                                               for i in range(self._params["total_steps"] + 1)])

            # TODO: Should this rather be stored in token_pair to make it easier to use with the analysis package?
            self.paths = pd.DataFrame(self._params["_paths"]).transpose()

        elif self.strategy == "merton_jump_diffusion":
            process = self.merton_jump_diffusion()

            for step in range(n_simulations):
                _path_generator = path_generator(
                    process, maturity, self._params["total_steps"])
                path = _path_generator.next().value()
                self._params["_paths"].append([path[i]
                                               for i in range(self._params["total_steps"] + 1)])

            # TODO: Should this rather be stored in token_pair to make it easier to use with the analysis package?
            self.paths = pd.DataFrame(self._params["_paths"]).transpose()
