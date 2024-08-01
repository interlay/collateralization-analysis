from substrateinterface import SubstrateInterface
import ssl
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)

urls = {
    "hydration": "wss://rpc.hydradx.cloud",
}


class Hydration_Token:
    """Class that represents a token"""

    def __init__(self, name: str, id: int, decimals: int):
        """Initializing the token object.

        Args:
            name (str): Name of the token which is used to identify the token in the data query so this must match the name of the token for the specific source.
            id (int): The Hydration identifier for the token in question.
        """
        self._id = id
        self._name = name
        self._decimals = decimals

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> int:
        return self._id
    
    @property
    def decimals(self) -> int:
        return self._decimals


# TODO: Add a default token argument that sets the quote currency to USD if nothing else is specified.
class Stableswap_Pair:
    """Class representating a trading pair of two tokens."""

    def __init__(
        self, 
        base_token: Hydration_Token, 
        quote_token: Hydration_Token,
        account: str,
        amplification: int,
        trade_fee: float,
        precision: float,
    ) -> None:
        """Initializing the token pair.

        Args:
            base_token (Token): A token that represent the base token of the trading pair.
                This can be seen as '1 unit of base token is worth x units of quote token'
            quote_token (Token): A second token that represents the quote token of the pair.
                This can be seen as 'x unit of quote token is worth 1 unit of base token'
        """
        self._base_token = base_token
        self._quote_token = quote_token
        self._account = account
        self._amplification = amplification
        self._trade_fee = trade_fee
        self._precision = precision
        self._price = None

    # Getter & Setter

    @property
    def base_token(self) -> Hydration_Token:
        return self._base_token

    @property
    def quote_token(self) -> Hydration_Token:
        return self._quote_token

    @property
    def account(self) -> int:
        return self._account

    @property
    def amplification(self) -> int:
        return self._amplification

    @property
    def trade_fee(self) -> float:
        return self._trade_fee

    @property
    def precision(self) -> float:
        return self._precision

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, price: float) -> None:
        self._price = price

    @property
    def returns(self) -> pd.DataFrame:
        return self._returns

    @returns.setter
    def returns(self, returns: pd.DataFrame) -> None:
        self._returns = returns

    # Functions
    def get_price(
        self,
        client: SubstrateInterface = SubstrateInterface(url=urls["hydration"], ws_options={'sslopt': {"cert_reqs": ssl.CERT_NONE}}),
        block_number: int = None,
        inverse: bool = False
    ) -> None:
        """Requests the prices from 'source'

        Args:
            data_source (str, optional): Source to get the data from. Defaults to "coingecko".
            start_date (str, optional): Start date as string in the format '%Y-%m-%d'. If none is given, the start date will be the end date - 365 days. Defaults to None.
            end_date (str, optional): End date as string in the format '%Y-%m-%d'. If none is given, it will default to today. Defaults to None.
            inverse (bool, optional): Coingecko does not support every token as quote currency. For exotic tokens as quote currency, this must be set to true so that the prices will be inverted. Defaults to False.
        """

        request = Hydration_Request(self, client, block_number)
        price = request.request_price()
        if not inverse:
            self.price = price
            return price
        else:
            self.price = 1 / price
            return 1 / price


# TODO: Implement coingecko API
class Hydration_Request:
    def __init__(
        self,
        token_pair: Stableswap_Pair,
        client: SubstrateInterface,
        block_number: int = None
    ):
        """
        :Token_Pair: An instance of class Token_Pair with the two tokens for which the data should be requested
        :data_source: Source from where the data should be requested
        :start_date: Start date as string in the format 'YYYY-MM-DD'
        :end_date: End date as string in the format 'YYYY-MM-DD', will default to today is not provided
        """

        self._token_pair = token_pair
        self._client = client
        self._block_number = block_number

    def fetch_current_block(self) -> int:
        result = self._client.query(
            module='System',
            storage_function='Number'
        )
        return result.value
    
    def fetch_blockhash_by_block_number(self, block_number: int) -> str:
        result = self._client.rpc_request(
            "chain_getBlockHash",
            [block_number]
        )
        return result['result']

    def request_token_balances(self):
        token_dict = {}
        for token in (self._token_pair._base_token, self._token_pair._quote_token):
            token_dict[token._id] = token
        balances = {}
        for k, dct in self._client.query_map(
            module="Tokens", 
            storage_function="Accounts",
            params=[self._token_pair.account],
            block_hash = self.fetch_blockhash_by_block_number(self._block_number)
        ):
            dct = dct.value_serialized
            token = token_dict[k.value_serialized]
            balance = dct.get('free')/ (10 ** token._decimals)

            balances[token._name] = balance
        return balances
    
    def request_price(self):
        if self._block_number is None:
            self.block_number = self.fetch_current_block()
        balances = self.request_token_balances()
        return self.price_at_balance([balances[self._token_pair._base_token._name], balances[self._token_pair._quote_token._name]])

    def calculate_d(self, balances, max_iterations=128) -> float:
        reserves = balances
        n_coins = len(balances)
        ann = self._token_pair._amplification * n_coins
        xp_sorted = sorted(reserves)
        s = sum(xp_sorted)
        if s == 0:
            return 0

        d = s
        for i in range(max_iterations):

            d_p = d
            for x in xp_sorted:
                d_p *= d / (x * len(balances))

            d_prev = d
            d = (ann * s + d_p * n_coins) * d / ((ann - 1) * d + (n_coins + 1) * d_p)

            if self.has_converged(d_prev, d):
                return d
            
    def has_converged(self, v0, v1) -> bool:
        diff = abs(v0 - v1)
        if (v1 <= v0 and diff < self._token_pair._precision) or (v1 > v0 and diff <= self._token_pair._precision):
            return True
        return False

    def price_at_balance(self, balances: list, i: int = 1, j: int = 0):
            n = len(balances)
            ann = self._token_pair._amplification * n
            d = self.calculate_d(balances)

            c = d
            sorted_bal = sorted(list(balances))
            for x in sorted_bal:
                c = c * d / (n * x)

            xi = balances[i]
            xj = balances[j]

            p = xj * (ann * xi + c) / (ann * xj + c) / xi

            return p
