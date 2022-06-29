from data_request import Token_Pair


class StrategyABC():
    def run(self):
        pass


class Montecarlo(StrategyABC):
    def __init__(self, ) -> None:
        pass

    def run(self, numbers_of_simulations):
        # code that runs the strategy
        pass


class jumpdiffusion(StrategyABC):
    def __init__(self, alpha=None) -> None:
        pass


class Simulation():
    def __init__(self, token_pair: Token_Pair, strategy: Strategy) -> None:
        self._token_pair = token_pair
        
    
    def simulate(self):
        #execute the strategy
        # pass paramters here
        strategy.run()
    
    
