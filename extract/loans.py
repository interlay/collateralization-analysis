from connections import extract_graphql, extract_substrate


async def extract_depositors(squid, height=None):
    """Extract depositors from the chain.

    Args:
        squid (str): The squid to query.
    Returns:
        list: The depositors as [{"userParachainAddress": "5D..."}, ...]
    """
    query = """
    {
      deposits(where: {type_eq: "lending"}) {
        userParachainAddress
      }
    }
    """
    deposits = await extract_graphql(squid, query)
    return deposits["deposits"]


async def extract_borrowers(squid, height=None):
    """Extract borrowers from the chain.

    Args:
        squid (str): The squid to query.
    Returns:
        list: The borrowers as [{"userParachainAddress": "5D..."}, ...]
    """
    query = """
    {
      loans(where: {amountBorrowed_isNull: false}) {
        userParachainAddress
      }
    }
    """
    borrows = await extract_graphql(squid, query)
    return borrows["loans"]


async def extract_deposits(squid):
    """Extracts all deposits and withdrawals to the lending protocol from the parachain.

    There are two types: lending and collateral.
    - Lending: means that an amount was either deposited (amountDeposited not null) or withdrawn (amountWithdrawn not null) into the lending protocol but that amount has not been added/removed as collateral.
    - Collateral: means that an amount was either deposited (amountDeposited not null) or withdrawn (amountWithdrawn not null) as collateral in the lending protocol.

    Note for collateral that first the user needs to deposit into lending via the "lending" type and only then can add it as collateral.

    Args:
      squid (str): The squid to query.

    Returns:
        dict: The deposits and withdrawals.
    """
    query = """
        query {
          deposits {
            type
            amountDeposited
            amountWithdrawn
            userParachainAddress
            token {
              ... on NativeToken {
                token
              }
              ... on ForeignAsset {
                asset
              }
              ... on LendToken {
                lendTokenId
              }
              ... on LpToken {
                token0 {
                  ... on NativeToken {
                    token
                  }
                  ... on ForeignAsset {
                    asset
                  }
                  ... on StableLpToken {
                    poolId
                  }
                }
                token1 {
                  ... on NativeToken {
                    token
                  }
                  ... on ForeignAsset {
                    asset
                  }
                  ... on StableLpToken {
                    poolId
                  }
                }
              }
              ... on StableLpToken {
                poolId
              }
            }
          }
        }
    """
    deposits = await extract_graphql(squid, query)
    return deposits
