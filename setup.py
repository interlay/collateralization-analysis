#%%
from chopsticks.state_queries import Kintsugi
from substrateinterface import Keypair, SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

kintsugi = Kintsugi()
# %%
kintsugi.remove_oracles()

# %%
