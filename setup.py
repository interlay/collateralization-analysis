#%%
from datetime import datetime
from substrateinterface import Keypair, SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

from extract.tokens import extract_onchain_tokens, extract_foreign_tokens
from chopsticks.dex import ChainDEX
from chopsticks.state_queries import ChainGeneral
from data.data_request import (
    Bitcoin_Dollar,
    BTC,
    KSM,
    USD,
    KINT,
    Token_Pair,
    ToBaseDecimals,
)

#%%
kintsugi = ChainGeneral()

#%%
kint, ksm, usd, btc = KINT(), KSM(), USD(), BTC()

ACCOUNT_FUNDING = {
    ksm: 100_000 * 10 ** ToBaseDecimals.KUSAMA.get_decimals(),
    kint: 100_000 * 10 ** ToBaseDecimals.KINTSUGI.get_decimals(),
}


kintsugi.fund_account(ACCOUNT_FUNDING)
# %%

kintsugi.get_thresholds()
kintsugi.get_total_stake()
kintsugi.get_registered_vaults()

#%%
btc_usd = Bitcoin_Dollar()
btc_usd.get_prices()
current_btc_price = btc_usd.prices.iloc[-1, 0]

ksm_usd = Token_Pair(ksm, kint)
ksm_usd.get_prices()
current_ksm_price = ksm_usd.prices.iloc[-1, 0]

kintsugi.update_collateral_ratios(ksm, current_ksm_price, current_btc_price)

# %%

dex = ChainDEX()
dex.exact_input_swap(100 * 10**12, 1)
# %%
