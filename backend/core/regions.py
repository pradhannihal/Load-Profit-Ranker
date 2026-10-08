"""EIA on-highway diesel regions (the `duoarea` facet of petroleum/pri/gnd).

Codes marked verified were confirmed against /v2/petroleum/pri/gnd/facet/duoarea
on 2026-10-06. Check the rest the same way before relying on them.
"""

REGIONS: dict[str, str] = {
    "NUS": "U.S. average",
    "R10": "East Coast (PADD 1)",  # verified
    "R1X": "New England (PADD 1A)",  # verified
    "R1Y": "Central Atlantic (PADD 1B)",  # verified
    "R1Z": "Lower Atlantic (PADD 1C)",  # verified
    "R20": "Midwest (PADD 2)",
    "R30": "Gulf Coast (PADD 3)",
    "R40": "Rocky Mountain (PADD 4)",
    "R50": "West Coast (PADD 5)",
    "SCA": "California",
}


def is_known_region(code: str) -> bool:
    return code in REGIONS
