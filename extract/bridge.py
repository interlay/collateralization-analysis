from connections import extract_substrate


async def extract_vaults(substrate, height=None):
    """Extract vaults from the chain."""
    vaults = await extract_substrate(substrate, "VaultRegistry", "Vaults", height)
    if "account_id" in vaults:
        # Remove the account_id key.
        return vaults["account_id"]
    return None


async def extract_issue_requests(substrate, height=None):
    """Extract issue requests from the chain."""
    issue_requests = await extract_substrate(
        substrate, "Issue", "IssueRequests", height
    )
    return issue_requests


async def extract_redeem_requests(substrate, height=None):
    """Extract redeem requests from the chain."""
    redeem_requests = await extract_substrate(
        substrate, "Redeem", "RedeemRequests", height
    )
    return redeem_requests


async def extract_replace_requests(substrate, height=None):
    """Extract replace requests from the chain."""
    replace_requests = await extract_substrate(
        substrate, "Replace", "ReplaceRequests", height
    )
    return replace_requests
