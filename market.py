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

    @property
    def base_token(self) -> Token:
        return self._base_token

    @property
    def quote_token(self) -> Token:
        return self._quote_token
    
    @property
    def invariant(self) -> int:
        return self._invariant

    def set_invariant(self) -> None:
        if self._type == "CPF":
            self._invariant = self._base_token_amount * self._quote_token_amount

    def exchange_rate(self) -> float:
        return float( self._quote_token_amount / self._base_token_amount)

    def add_liquidity(self, amount: int) -> None:
        """Adds liquidity too the pool.

        Args:
            amount (int): The amount is the value to be added, in units of the quote currency that will be split 50/50 between boths tokens.
            E.g. if the quote currency is USD, as in a BTC/USD quote, the value is in USD. If the quote currency is something else like BTC/DOT
            the amount would be the amount of DOTs added to the pool (which will be split 50/50 still).
        """
        self._base_token_amount += amount / 2 / self.exchange_rate()
        self._quote_token_amount += amount / 2
        self.set_invariant()

    def remove_liquidity(self, amount: int) -> None:
        """Adds liquidity too the pool.

        Args:
            amount (int): The amount is the value to be removed, in units of the quote currency that will be split 50/50 between boths tokens.
            E.g. if the quote currency is USD, as in a BTC/USD quote, the value is in USD. If the quote currency is something else like BTC/DOT
            the amount would be the amount of DOTs added to the pool (which will be split 50/50 still).
        """
        self._base_token_amount -= amount / 2 / self.exchange_rate()
        self._quote_token_amount -= amount / 2
        self.set_invariant()

    # TODO: refacture swap and calculate_slippage!

    def exact_output_swap(self, output_token: Token, amount: int) -> float:
        """Executes an exact output swap.

        Args:
            amount (int): Amount of 'output_token' to swap (buy from the pool)
            output_token (Token): The token to receive as the output of the swap.

        Raises:
            Exception: Raises and error if swap amount is too large.

        Returns:
            float: _description_
        """
        if output_token.name == self.base_token.name:
            # does the swap with the base token as output
            if amount < self._base_token_amount:
                self._previous_exchange_rate = self.exchange_rate()
                self._base_token_amount = self.base_token_amount - amount
                self._quote_token_amount = self.invariant / self._base_token_amount

                return float( self.exchange_rate() / self._previous_exchange_rate - 1)
            else:
                raise Exception(
                    "Swap amount must be smaller than the amount of base tokens in the pool.")

        else:
            # does the swap with the quote token as output
            if amount < self._quote_token_amount:
                self._previous_exchange_rate = self.exchange_rate()
                self._quote_token_amount = self._quote_token_amount + amount
                self._base_token_amount = self.invariant / self._quote_token_amount

                return float( self.exchange_rate() / self._previous_exchange_rate - 1)
            else:
                raise Exception(
                    "Swap amount must be smaller than the amount of base tokens in the pool.")


    def exact_input_swap(self, input_token: Token, amount: int) -> float:
        """Executes and exacpt input swap.

        Args:
            amount (int): Amount of 'input_token' to swap (sell to the pool)
            input_token (Token): The token to send to the pool as the input of the swap.

        Returns:
            float: _description_
        """
        if input_token.name == self.base_token.name:
            self._previous_exchange_rate = self.exchange_rate()
            self._base_token_amount = self.base_token_amount + amount
            self._quote_token_amount = self.invariant / self._base_token_amount

            return float( self.exchange_rate()  / self._previous_exchange_rate- 1)
        else:
            self._previous_exchange_rate = self.exchange_rate()
            self._quote_token_amount = self._quote_token_amount + amount
            self._base_token_amount = self.invariant / self._quote_token_amount

            return float( self.exchange_rate()  / self._previous_exchange_rate- 1)


    def calculate_params(self, token: Token, amount: int, type: str = "exact_output") -> tuple(float, float, float):
        if (token.name == self.base_token.name) & (type == "exact_output"):
            # does the swap with the base token as output
            if amount < self._base_token_amount:
                _previous_exchange_rate = self.exchange_rate()
                _base_token_amount = self.base_token_amount - amount
                _quote_token_amount = self.invariant / self._base_token_amount
                _slippage = float( self.exchange_rate() / self._previous_exchange_rate - 1)
            else:
                raise Exception(
                    "Swap amount must be smaller than the amount of base tokens in the pool.")
            
        elif (token.name == self.quote_token.name) & (type == "exact_output"):
            if amount < self._quote_token_amount:
                _previous_exchange_rate = self.exchange_rate()
                _quote_token_amount = self._quote_token_amount - amount
                _base_token_amount = self.invariant / self._quote_token_amount
            else:
                raise Exception(
                    "Swap amount must be smaller than the amount of base tokens in the pool.")
            
        elif (token.name == self.base_token.name) & (type == "exact_input"):
            # does the swap with the base token as output
                _previous_exchange_rate = self.exchange_rate()
                _base_token_amount = self.base_token_amount + amount
                _quote_token_amount = self.invariant / self._base_token_amount
                _slippage = float( self.exchange_rate() / self._previous_exchange_rate - 1)

            
        elif (token.name == self.quote_token.name) & (type == "exact_input"):
                _previous_exchange_rate = self.exchange_rate()
                _quote_token_amount = self._quote_token_amount + amount
                _base_token_amount = self.invariant / self._quote_token_amount
                
                
        return (_base_token_amount, _quote_token_amount, _slippage)