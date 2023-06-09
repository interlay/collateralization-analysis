import asyncio
from pprint import pprint

from connections import extract_substrate
from tokens import extract_lending_tokens


async def extract_user_accounts(substrate, details=False, height=None):
    """
    Get all accounts of users on the chain.

    Returns:
        A list of user accounts.
    """
    accounts_info = await extract_substrate(
        substrate, "System", "Account", height=height
    )
    if details:
        return accounts_info
    return list(accounts_info.keys())


async def extract_user_portfolios(substrate, accounts, height=None):
    """
    Get all portfolio values of users at a start height. The portfolios consists of two parts:
    - All on-chain tokens (assets)
    - All on-chain loans (liabilities)

    Args:
        accounts: A list of user accounts.

    Returns:
      A list of user portfolios with their on-chain tokens.
    """
    [assets, liabilities] = await asyncio.gather(
        extract_user_assets(substrate, accounts, height),
        extract_user_liabilities(substrate, accounts, height),
    )
    return merge_assets_and_liabilities(assets, liabilities)


def merge_assets_and_liabilities(assets, liabilities):
    """
    Merge assets and liabilities into a single portfolio.

    Args:
        assets: A list of user portfolios with their on-chain tokens.
        liabilities: A list of user portfolios with their on-chain loans.

    Returns:
        A list of user portfolios with their on-chain tokens and loans.
    """

    user_portfolios = assets
    for user in liabilities:
        for token_type, token_amounts in liabilities[user].items():
            for token, amount in token_amounts.items():
                if user not in user_portfolios:
                    user_portfolios[user] = {}
                if token_type not in user_portfolios[user]:
                    user_portfolios[user][token_type] = {}
                if token not in user_portfolios[user][token_type]:
                    user_portfolios[user][token_type][token] = 0
                user_portfolios[user][token_type][token] = (
                    user_portfolios[user][token_type][token] - amount
                )

    pprint(user_portfolios)
    return user_portfolios


async def extract_user_assets(substrate, accounts, height=None):
    """
    Get all assets of users at a start height.

    Args:
        accounts: A list of user accounts.

    Returns:
        A list of user assets.
    """
    # The assets of the user
    asset_tasks = []
    for account in accounts:
        asset_tasks.append(
            extract_substrate(substrate, "Tokens", "Accounts", [account], height)
        )
    assets = await asyncio.gather(*asset_tasks)
    # Sum all token balances
    portfolios_aggregate = []
    for portfolio in assets:
        portfolio_aggregate = {}
        for token_type, balances in portfolio.items():
            for token, balance in balances.items():
                # Convert foreign asset, lend token, and stable lp keys to int
                if (
                    token_type == "ForeignAsset"
                    or token_type == "LendToken"
                    or token_type == "StableLpToken"
                ):
                    token = int(token)
                # check if token type key exists and add if not
                if token_type not in portfolio_aggregate:
                    portfolio_aggregate[token_type] = {}
                portfolio_aggregate[token_type][token] = sum(balance.values())
        portfolios_aggregate.append(portfolio_aggregate)

    asset_values = dict(zip(accounts, portfolios_aggregate))

    return asset_values


async def extract_user_liabilities(substrate, accounts, height=None):
    """
    Get all liabilities of users at a start height.

    Returns:
        A list of user liabilities.
    """
    # The loans.accountBorrows.principal is without interest, you need to use the loans.accountBorrows.borrow_index and the global loans.BorrowIndex to determine the amount with interest
    # Specifically, borrow_with_interest = loans.accountBorrows.principal * loans.BorrowIndex / loans.accountBorrows.borrow_index. That assumes the global loans.borrowIndex is up to date but that's fine I think for the script program

    # The liabilities of users
    [lending_tokens, borrow_index] = await asyncio.gather(
        extract_lending_tokens(substrate, height),
        extract_substrate(substrate, "Loans", "BorrowIndex", height),
    )
    if not borrow_index:
        return {}

    # Convert foreign asset ids to int
    foreign_asset_index = {int(k): v for k, v in borrow_index["ForeignAsset"].items()}
    borrow_index["ForeignAsset"] = foreign_asset_index

    liabilities_tasks = []
    token_index = list(lending_tokens["LendToken"].values())
    for token in token_index:
        liabilities_tasks.append(
            extract_substrate(substrate, "Loans", "AccountBorrows", [token], height)
        )
    liabilities = await asyncio.gather(*liabilities_tasks)

    liability_values = {}
    # Calculate the borrow_with_interest
    for i in range(len(liabilities)):
        token, identifier = next(iter(token_index[i].items()))
        global_borrow_index = borrow_index[token][identifier]
        for account, info in liabilities[i].items():
            if account in accounts:
                user_borrow_index = info["borrow_index"]
                principal = info["principal"]
                borrow_with_interest = (
                    principal * global_borrow_index / user_borrow_index
                )
                if account not in liability_values:
                    liability_values[account] = {}
                liability_values[account][token] = {identifier: borrow_with_interest}

    return liability_values


def transform_portfolio_values_to_usd(user_portfolios, exchange_rates):
    """
    Transform all portfolio values to USD.

    Returns:
      A list of user portfolios with their USD values.
    """
    pprint(user_portfolios)
    pprint(exchange_rates)
    user_usd_portfolios = {}
    for account, portfolio in user_portfolios.items():
        user_usd_portfolio = []
        for token_type, amounts in portfolio.items():
            for token, amount in amounts.items():
                try:
                    value = amount * exchange_rates[token_type][token]["usdRate"]
                    user_usd_portfolio.append(value)
                except KeyError:
                    print("{} {} not found in exchange rates".format(token_type, token))
                    continue
                except TypeError:
                    print("{} {} not found in exchange rates".format(token_type, token))
                    continue
        user_usd_portfolios[account] = sum(user_usd_portfolio)

    pprint(user_usd_portfolios)
    return user_usd_portfolios
