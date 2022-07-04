import pytest
from data.data_request import Token

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

