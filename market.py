from data_request import Token


class Automted_Market_Maker():
    """
    This class simulates an AMM
    """

    def __init__(self, base_token: Token, quote_token: Token,  base_token_amount: int, quote_token_amount: int, type: str = "CPF"):
        self._base_token = base_token
        self._quote_token = quote_token
        self._base_token_amount = base_token_amount
        self._quote_token_amount = quote_token_amount
        self._type = type
        self._invariant = self._base_token_amount * self._quote_token_amount

    @property
    def invariant(self) -> int:
        return self._invariant

    @property
    def base_token_amount(self) -> int:
        return self._base_token_amount

    @property
    def quote_token_amount(self) -> int:
        return self._quote_token_amount

    @invariant.setter
    def invariant(self) -> None:
        if self._type == "CPF":
            self._invariant = self._base_token_amount * self._quote_token_amount

    def exchange_rate(self) -> float:
        return float(self._base_token_amount / self._quote_token_amount)

    # TODO: refacture swap and calculate_slippage!
    def swap(self, amount) -> float:
        if amount < self._base_token_amount:
            self._previous_exchange_rate = self.exchange_rate()
            self._base_token_amount = self.base_token_amount + amount
            self._quote_token_amount = self.invariant / self._base_token_amount

            return float(self._previous_exchange_rate / self.exchange_rate() - 1)
        else:
            raise Exception(
                "Swap amount must be smaller than the amount of base tokens in the pool.")

    def calculate_slippage(self, amount: float) -> float:
        if amount < self._base_token_amount:
            _previous_exchange_rate = self.exchange_rate()
            _base_token_amount = self.base_token_amount + amount
            _quote_token_amount = self.invariant / self._base_token_amount
            _exchange_rate = _base_token_amount / _quote_token_amount
            return float(_previous_exchange_rate / _exchange_rate - 1)
        else:
            raise Exception(
                "Swap amount must be smaller than the amount of base tokens in the pool.")
