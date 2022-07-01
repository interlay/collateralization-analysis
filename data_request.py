import requests
from datetime import datetime
import pandas as pd

urls = {
    "coingecko": "https://api.coingecko.com/api/v3/coins/",
}

class Token():
    def __init__(self, name:str, ticker: str):
        self._ticker = ticker
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def ticker(self) -> str:
        return self._ticker


class Token_Pair():
    def __init__(self, base_token: Token, quote_token: Token) -> None:
        self._base_token = base_token
        self._quote_token = quote_token

    # Getter & Setter

    @property
    def base_token(self) -> Token:
        return self._base_token

    @property
    def quote_token(self) -> Token:
        return self._quote_token

    @property
    def prices(self) -> pd.DataFrame:
        return self._prices

    @prices.setter
    def prices(self, prices: pd.DataFrame) -> None:
        self._prices = prices

    @property
    def returns(self) -> pd.DataFrame:
        return self._returns

    @returns.setter
    def returns(self, returns):
        self._returns = returns


    # Functions

    def get_prices(self, data_source: str = "coingecko", start_date: str = None, end_date: str = None, inverse: bool=False) -> None:
        """Requests the prices from 'source' 

        Args:
            data_source (str, optional): Source to get the data from. Defaults to "coingecko".
            start_date (str, optional): Start date as string in the format '%Y-%m-%d'. If none is given, the start date will be the end date - 365 days. Defaults to None.
            end_date (str, optional): End date as string in the format '%Y-%m-%d'. If none is given, it will default to today. Defaults to None.
            inverse (bool, optional): Coingecko does not support every token as quote currency. For exotic tokens as quote currency, this must be set to true so that the prices will be inverted. Defaults to False.
        """
        
        request = Data_Request(self, data_source, start_date, end_date)
        prices = request.request_historic_prices()
        if not inverse:
            self.prices = prices
        else:
            self.prices = 1 / prices

    def calculate_returns(self, type: str = "geometric", period: str = "daily") -> None:
        shift_periods = {
            "daily": 1,
            "weekly" : 7,
            "monthly": 31,
            "yearly": 365
        }
        shift_period = shift_periods[period]

        if type == "geometric":
            self.returns = self.prices.pct_change(periods=shift_period, fill_method="bfill").dropna()


class Data_Request():
    def __init__(self, token_pair: Token_Pair, data_source: str ="coingecko", start_date: str = None, end_date: str = None):
        """
        :Token_Pair: An instance of class Token_Pair with the two tokens for which the data should be requested
        :data_source: Source from where the data should be requested
        :start_date: Start date as string in the format 'YYYY-MM-DD'
        :end_date: End date as string in the format 'YYYY-MM-DD', will default to today is not provided
        """

        self._token_pair = token_pair
        self._data_source = data_source
        self._start_date = start_date
        self._end_date = end_date if end_date is not None else datetime.today().strftime("%Y-%m-%d")

    def get_length_in_days(self) -> str:
        if self._start_date is None:
            return str(365)
        
        time_delta = datetime.strptime(self._end_date, "%Y-%m-%d") - datetime.strptime(self._start_date, "%Y-%m-%d")
        return str(time_delta.days)

    def parse_url(self):
        "Currently only supports price requests from coingecko"

        length_in_days = self.get_length_in_days()

        if self._data_source == "coingecko":
            base_token = self._token_pair.base_token.name
            quote_token = self._token_pair.quote_token.name
            self._url_endpoint = urls[self._data_source] + base_token + "/market_chart?vs_currency=" + quote_token + "&days=" + length_in_days

    def request_historic_prices(self):
        self.parse_url()
        price_data = requests.get(self._url_endpoint).json()["prices"]
        price_data = pd.DataFrame(price_data, columns=["Date", "Price"])
        price_data.set_index("Date", inplace=True)
        price_data.index = pd.to_datetime(price_data.index, unit="ms")
        return price_data
