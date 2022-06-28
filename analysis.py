from matplotlib import pyplot as plt
from data_request import Token_Pair

class Analysis():
    def __init__(self, token_pair: Token_Pair):
        self.token_pair = token_pair

    def plot_returns(self, data_label, title):
        plt.hist(self.token_pair.returns, density=True, bins=30, alpha=0.5, label=data_label)
        plt.ylabel("Occurences")
        plt.xlabel("Percentage change")
        plt.legend(loc="upper right")
        plt.title(title)
