async def get_current_height(substrate):
    """Get the current height of the chain."""
    current_header = substrate.get_block_header()
    return current_header["header"]["number"]
