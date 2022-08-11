import pytest
from unit_tests.conftest import DOT_USD
from simulation.simulation import Simulation
import QuantLib as ql


@pytest.mark.parametrize(
    "strategy", ["GBM", "merton_jump_diffusion", "heston_process", "black_process"]
)
def test_can_simulate_process(strategy: str, DOT_USD):
    simulation = Simulation(token_pair=DOT_USD, strategy=strategy)

    # the parameters dont matter and were set low to make it computationally inexpensive
    simulation.simulate(
        steps=10,
        maturity=1,
        n_simulations=10,
        sigma=1,
        mu=0,
        initial_value=1,
    )

    # results are stored in self.paths as df so this should exist
    assert simulation.paths.shape[0] == 11
    assert simulation.paths.shape[1] == 10
