from data.data_request import Token_Pair
import QuantLib as ql
import numpy as np
from datetime import datetime
import pandas as pd


def parse_date_to_quantlib(date: pd.Timestamp) -> ql.Date:
    """Parses a pandas.Timestamp object into a quantLib.Date object.

    Args:
        date (pd.Timestamp): Timestamp object to parse.

    Returns:
        ql.Date: quantLib.Date object for the simulation.
    """
    date = datetime.strftime(date, "%d-%m-%Y")
    return ql.Date(*[int(i) for i in date.split("-")])

def path_generator(process, maturity: float, nSteps: int):
    """Returns a path generator for any process by first, generating a uniform_sequence_generator for the given dimensions.
    Secondly, it creates a gaussian_sequence_generator, using the uniform_sequence_generator. Lastly it returns a GaussianMultiPathGenerator iterator-object,
    which can be used to generate random paths using the given process.

    Args:
        process (_type_): _description_
        maturity (_type_): The maruity at which the process ends. This can be though of as how many times the number of steps will be run by the simulation.
            E.g. if you have steps that represent one day, you can create a time series with the maturity of two years by using 365 steps and a maturity of 2.
        nSteps (_type_): The number of steps within one period of the maturity. The unit is determined by the time units of the sample. 
            E.g. if you have estimate the mean and standard deviation from a sample of daily data, each step will be generated based on those values.

    Returns:
        _type_: _description_
    """
    dimensions = process.factors()
    times = ql.TimeGrid(maturity, nSteps)

    unifrom_sequence_generator = ql.UniformRandomSequenceGenerator(
        dimensions * nSteps, ql.UniformRandomGenerator()
    )
    gaussian_sequence_generator = ql.GaussianRandomSequenceGenerator(
        unifrom_sequence_generator
    )
    return ql.GaussianMultiPathGenerator(
        process, list(times), gaussian_sequence_generator, False
    )
class Simulation:
    """This class represents a simulation with different processes.
    """

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
        riskFreeTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"],
                           0.05, ql.Actual365Fixed())
        )
        volTS = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(
                self._params["start_date"],
                ql.NullCalendar(),
                self._params["sigma"],
                ql.Actual365Fixed(),
            )
        )
        return ql.BlackProcess(self._params["initial_value"], riskFreeTS, volTS)

    def geometric_brownian_motion(self) -> ql.GeometricBrownianMotionProcess:
        return ql.GeometricBrownianMotionProcess(
            # I dont understand why this fails without .value()
            self._params["initial_value"].value(),
            self._params["mu"],
            self._params["sigma"],
        )

    # TODO: Pass the hard coded values as args or kwargs
    def heston_process(self) -> ql.Merton76Process:
        riskFreeTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"],
                           0.05, ql.Actual365Fixed())
        )
        dividendTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"],
                           0.01, ql.Actual365Fixed())
        )

        v0, kappa, theta, rho, sigma = 0.005, 0.8, 0.008, 0.2, self._params["sigma"]
        return ql.HestonProcess(
            riskFreeTS,
            dividendTS,
            self._params["initial_value"],
            v0,
            kappa,
            theta,
            sigma,
            rho,
        )

    def merton_jump_diffusion(self) -> ql.Merton76Process:
        dividendTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"],
                           0.02, ql.Actual365Fixed())
        )
        riskFreeTS = ql.YieldTermStructureHandle(
            ql.FlatForward(self._params["start_date"],
                           0.01, ql.Actual365Fixed())
        )
        volTS = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(
                self._params["start_date"],
                ql.NullCalendar(),
                self._params["sigma"],
                ql.Actual365Fixed(),
            )
        )

        jumpIntensity = ql.QuoteHandle(ql.SimpleQuote(1.0))
        jumpVolatility = ql.QuoteHandle(
            ql.SimpleQuote(
                self._params["sigma"] * np.sqrt(0.25 / jumpIntensity.value())
            )
        )
        meanLogJump = ql.QuoteHandle(
            ql.SimpleQuote(-jumpVolatility.value() * jumpVolatility.value())
        )

        return ql.Merton76Process(
            self._params["initial_value"],
            dividendTS,
            riskFreeTS,
            volTS,
            jumpIntensity,
            meanLogJump,
            jumpVolatility,
        )

    def simulate(
        self,
        steps: int,
        maturity: int,
        n_simulations: int = 10_000,
        sigma: float = None,
        mu: float = None,
        initial_value: float = None,
    ) -> None:
        """
        Given the time unit is days, the default arguments represent a path with a length of 1 year, consisting of 365 days.
        1000 of those paths will be simulated.

        Args:
            steps (int): Steps within a period of the maturity.
            maturity (int): Maturity periods determining the length of the simulation.
            n_simulations (int, optional): Number of paths to be simulated. Defaults to 10,000.
            sigma (float, optional): The standard deviation of the random processes. If None, it defaults to the standard deviation of the sample.
            mu (float, optional): The mean drift of the random process. If None it defaults to the mean of the sample. 
            initial_value (float, optional): The initial value of the random process. If None, it defaults to the initial value of the sample.

        Returns:
            None
        """

        self._params = {
            "sigma": sigma if sigma else self.token_pair.returns.std()[0],
            "mu": mu if mu else self.token_pair.returns.mean()[0],
            "initial_value": ql.QuoteHandle(
                ql.SimpleQuote(
                    initial_value if initial_value else self.token_pair.prices.iloc[0][0])
            ),
            "start_date": parse_date_to_quantlib(self.token_pair.prices.index[0]),
            "total_steps": int(maturity * steps),
            "_paths": [],
        }

        # TODO: Refactor this to allow more flexibility
        if self.strategy == "GBM":
            process = self.geometric_brownian_motion()
        elif self.strategy == "merton_jump_diffusion":
            process = self.merton_jump_diffusion()
        elif self.strategy == "heston_process":
            process = self.heston_process()
        elif self.strategy == "black_process":
            process = self.black_process()

        _path_generator = path_generator(
            process, maturity, self._params["total_steps"]
        )
        # TODO: should this be refactored? If so, how?
        for _ in range(n_simulations):
            path = _path_generator.next().value()
            self._params["_paths"].append(
                [path[0][i] for i in range(self._params["total_steps"] + 1)]
            )

        # TODO: Should this rather be stored in token_pair to make it easier to use with the analysis package?
        self.paths = pd.DataFrame(self._params["_paths"]).transpose()
