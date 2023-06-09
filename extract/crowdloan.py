from connections import extract_substrate


async def extract_vesting_schedules(substrate, height=None):
    """Extract vesting schedules from the chain."""
    vesting_schedules = await extract_substrate(
        substrate, "Vesting", "VestingSchedules", height
    )
    return vesting_schedules
