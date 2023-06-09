from connections import extract_graphql
from users import extract_user_accounts, extract_user_assets


async def extract_trade_count_per_account(squid):
    """Extracts the number of trades per account.

    Args:
      squid (str): The squid to query.

    Returns:
        list: The number of trades per account as [{"accountId": "5D...", "count": 123}, ...]
    """
    query = """
    {
      cumulativeDexTradeCountPerAccounts {
        accountId
        count
      }
    }
    """
    trades = await extract_graphql(squid, query)
    return trades["cumulativeDexTradeCountPerAccounts"]


async def extract_liquidity_provision(substrate, accounts=None):
    """Extracts the liquidity provision.

    Args:
      substrate (SubstrateInterface): The substrate interface to convert the raw address to a SS58 address.
      accounts (list): A list of user accounts.

    Returns:
        dict: The number of different pairs a user provided liquidity to provisions as {"5D...": 2, ...}
    """
    # TODO: this should be refactored and use squid instead of the very expensive on-chain queries

    if not accounts:
        accounts = await extract_user_accounts(substrate)
    user_assets = await extract_user_assets(substrate, accounts)

    liquidity_provision = {}
    for account, assets in user_assets.items():
        # Skip users that don't have LP tokens
        if "LpToken" not in assets and "StableLpToken" not in assets:
            continue

        num_pairs = 0
        if "LpToken" in assets:
            num_pairs += len(assets["LpToken"])
        if "StableLpToken" in assets:
            num_pairs += len(assets["StableLpToken"])
        liquidity_provision[account] = num_pairs

    return liquidity_provision
