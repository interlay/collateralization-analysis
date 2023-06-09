from connections import extract_substrate


async def extract_collators(substrate, height=None):
    """Extract collators from the chain."""
    collators = substrate.query("CollatorSelection", "Candidates")
    return collators.serialize()
