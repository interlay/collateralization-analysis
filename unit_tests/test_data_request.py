import pytest
from ..data.data_request import Token, Token_Pair, Data_Request
from unit_tests.conftest import *

@pytest.mark.parametrize(
    "name, ticker", 
    [("acala-dollar", "aUSD"), ("bitcoin", "BTC"), ("polkadot", "DOT")])
def test_can_create_token(name: str, ticker: str):
    t = Token(name, ticker)
    breakpoint()
    assert t.name == name
    assert t.ticker == ticker
    
    
@pytest.mark.parametrize(
    "base_token",
    [aUSD, BTC, DOT]
)
@pytest.mark.parametrize("quote_token", [USD])
def test_can_create_token_pair(base_token: Token, quote_token: Token):
    breakpoint()
    pair = Token_Pair(base_token, quote_token)
    assert pair.base_token.name == base_token.name
    assert pair.quote_token == quote_token.name

    
@pytest.mark.parametrize(
    "base_token",
    [aUSD, BTC, DOT]
)
@pytest.mark.parametrize("quote_token", [USD])
def test_can_query_coingecko_prices(base_token: Token, quote_token: Token):
    pair = Token_Pair(base_token, quote_token)
    pair.get_prices(data_source="coingecko")
    
    assert pair.prices
    

@pytest.mark.parametrize(
    "base_token, quote_token",
    [(BTC, USD), (DOT,USD)]
)
@pytest.mark.parametrize("period",
    ["daily", "weekly", "monthly", "annualy"])
def test_can_calculate_geometric_returns(base_token: Token, quote_token: Token, period: str):
    pair = Token_Pair(base_token, quote_token)
    pair.get_prices(data_source="coingecko")
    
    pair.calculate_returns(period = period)
    
    assert pair.returns
