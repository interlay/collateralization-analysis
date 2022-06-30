from importlib.resources import path
from data_request import Token_Pair
import QuantLib as ql
import numpy as np
from datetime import datetime
import pandas as pd


def parse_date_to_quantlib(self, date: str) -> ql.Date:
    date = datetime.strftime(date,  "%d-%m-%Y")
    return ql.Date(*[int(i) for i in date.split("-")])


def path_generator(process, maturity, nSteps):
    generator = ql.UniformRandomGenerator()
    sequenceGenerator = ql.UniformRandomSequenceGenerator(
        nSteps, generator)
    gaussianSequenceGenerator = ql.GaussianRandomSequenceGenerator(
        sequenceGenerator)
    path_generator = ql.GaussianPathGenerator(
        process, maturity, nSteps, gaussianSequenceGenerator, False)
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
        # get std as int
        _sigma = self.token_pair.returns.std()[0]
        _mu = 0
        # get first price of the dataframe as int
        _initial_value = self.token_pair.prices.iloc[0][0]
        return ql.GeometricBrownianMotionProcess(
            _initial_value, mu=_mu, sigma=_sigma)

    def simulate(self, steps: int = 365, maturity: int = 1, n_simulations: int = 50, type="returns", **kwargs) -> None:
        """
        Given the time unit is days, the default arguments represent a path with a length of 1 year, consisting of 365 days. 
        1000 of those paths will be simulated.

        Args:
            steps (int, optional): Steps within a period of the maturity. Defaults to 365, which could be a year if the time unit is days.
            maturity (int, optional): Maturity periods determining the length of the simulation. Defaults to 1.
            n_simulations (int, optional): _description_. Defaults to 1000.
        """
        # TODO: Refactor this to allow more flexibility
        if self.strategy == "GMB":
            process = self.geometric_brownian_motion()

            total_steps = int(maturity * steps)
            _paths = []
            for step in range(n_simulations):
                _path_generator = path_generator(
                    process, maturity, total_steps)
                path = _path_generator.next().value()
                _paths.append([path[i]
                               for i in range(total_steps + 1)])

            # TODO: Should this rather be stored in token_pair to make it easier to use with the analysis package?
            self.paths = pd.DataFrame(_paths).transpose()
