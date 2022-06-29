from data_request import Token_Pair
import QuantLib as ql
import numpy as np
from datetime import datetime


def parse_date_to_quantlib(self, date: str) -> ql.Date:
    date = datetime.strftime(date,  "%d-%m-%Y")
    return ql.Date(*[int(i) for i in date.split("-")])


def GeneratePaths(process, maturity, nPaths, nSteps):
    generator = ql.UniformRandomGenerator()
    sequenceGenerator = ql.UniformRandomSequenceGenerator(
        nSteps, generator)
    gaussianSequenceGenerator = ql.GaussianRandomSequenceGenerator(
        sequenceGenerator)
    paths = np.zeros(shape=((nPaths), nSteps + 1))
    pathGenerator = ql.GaussianPathGenerator(
        process, maturity, nSteps, gaussianSequenceGenerator, False)
    for i in range(nPaths):
        path = pathGenerator.next().value()
        paths[i, :] = np.array([path[j] for j in range(nSteps + 1)])
    return paths


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

    def geometric_brownian_motion(self, **kwargs):
        # get std as int
        _sigma = self.token_pair.returns.std()[0]
        _mu = 0
        # get first price of the dataframe as int
        _initial_value = self.token_pair.prices.iloc[0][0]
        process = ql.GeometricBrownianMotionProcess(
            _initial_value, mu=_mu, sigma=_sigma)

        maturity = 3.0
        nPaths = 50
        nSteps = int(maturity * 365)
        paths = GeneratePaths(process, maturity, nPaths, nSteps)

        # start_date = parse_date_to_quantlib(self.token_pair.prices.index[0])
        # ql.Settings_instance().evaluationDate = start_date
        # dayCounter = ql.Actual360()
        # calendar = ql.UnitedStates()
        # settlementDate = calendar.advance(start_date, 0, ql.Days)

    # process = QuantLib 1-dimensional stochastic process object

    def simulate(self, **kwargs):
        # execute the strategy
        # pass paramters here
        if self.strategy == "GMB":
            _sigma = self.token_pair.returns.std()[0]
            _mu = 0
            _initial_value = self.token_pair.prices.iloc[0][0]
            process = ql.GeometricBrownianMotionProcess(
                _initial_value, mu=_mu, sigma=_sigma)
            maturity = 3.0
            nPaths = 50
            nSteps = int(maturity * 365)
            self.paths = GeneratePaths(process, maturity, nPaths, nSteps)
