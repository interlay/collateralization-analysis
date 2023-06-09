from connections import extract_substrate


async def extract_stakers(substrate, height=None):
    """Extract stakers from the chain."""
    stakers = await extract_substrate(substrate, "Escrow", "Locked", height)
    return stakers


async def extract_votes(substrate, height=None):
    """Extract votes from the chain."""
    votes = await extract_substrate(substrate, "Democracy", "VotingOf", height)
    return votes
