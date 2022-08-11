import pytest
from data.data_request import Token, Token_Pair


@pytest.fixture(scope="module")
def USD():
    yield Token("usd", "USD")


@pytest.fixture(scope="module")
def aUSD():
    yield Token("acala-dollar", "aUSD")


@pytest.fixture(scope="module")
def BTC():
    yield Token("bitcoin", "BTC")


@pytest.fixture(scope="module")
def DOT():
    yield Token("polkadot", "DOT")


@pytest.fixture(scope="module")
def DOT_USD():
    pair = Token_Pair(Token("polkadot", "DOT"), Token("dollar", "USD"))
    pair.get_prices(start_date="2020-08-19")
    pair.calculate_returns()
    yield pair
