from data_request import Token_Pair


class StrategyABC():
    def run(self):
        pass


class Strategy(StrategyABC):
    def __init__(self) -> None:
        pass

    def run(self):
        # code that runs the strategy
        pass

class Simulation():
    def __init__(self, token_pair: Token_Pair, strategy: Strategy) -> None:
        self._token_pair = token_pair
        self._strategy = strategy
        
        
    def simulate(self):
        #execute the strategy
        pass
    
    
