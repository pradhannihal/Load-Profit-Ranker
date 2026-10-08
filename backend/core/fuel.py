"""Parse EIA API v2 weekly diesel responses. Pure: no network, no clock."""

from dataclasses import dataclass
from datetime import date

STALE_AFTER_DAYS = 10  # PLAN risk #7: warn if the cached price is older than this


class FuelParseError(ValueError):
    """The EIA response didn't contain a usable price."""


@dataclass(frozen=True)
class FuelPrice:
    region: str
    price: float  # $/gal
    as_of: date  # EIA's `period`, the week the price is for (not when we fetched it)
    series: str


def parse_eia_response(body: dict) -> FuelPrice:
    """Take the newest row from a /petroleum/pri/gnd/data response.

    EIA returns `value` as a string, and sends an "incomplete return" warning
    even for length=1, so `warnings` is ignored.
    """
    try:
        rows = body["response"]["data"]
    except (KeyError, TypeError) as e:
        raise FuelParseError("No response.data in EIA body") from e
    if not rows:
        raise FuelParseError("EIA returned no rows")

    row = max(rows, key=lambda r: r.get("period", ""))
    try:
        price = float(row["value"])
        as_of = date.fromisoformat(row["period"])
        region = row["duoarea"]
    except (KeyError, TypeError, ValueError) as e:
        raise FuelParseError(f"Bad EIA row: {row!r}") from e
    if price <= 0:
        raise FuelParseError(f"Non-positive diesel price: {price}")
    return FuelPrice(region=region, price=price, as_of=as_of, series=row.get("series", ""))


def is_stale(as_of: date, today: date, max_age_days: int = STALE_AFTER_DAYS) -> bool:
    return (today - as_of).days > max_age_days
