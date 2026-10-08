"""JSON <-> engine objects. The ONLY place camelCase and snake_case meet.

The JSON names match docs/formula.md (camelCase); the engine uses snake_case.
Used by the local Flask app now and by the Lambda handlers in M4.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import date
from typing import Any

from core.config import DEFAULTS, EngineConfig
from core.models import Issue, LoadInput, Ranking, TripContext, TruckSettings, WhyLine
from core.regions import is_known_region

MAX_LOADS_IN_REQUEST = 10  # validation allows 3; this just stops huge bodies early

# JSON name under truckSettings.advanced -> EngineConfig field
_ADVANCED = {
    "avgSpeedMph": "avg_speed_mph",
    "bufferHours": "buffer_hours",
    "workingDaysPerMonth": "working_days_per_month",
    "maxCycleHours": "max_cycle_hours",
}


def to_camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part.title() for part in rest)


def field_to_json(path: str) -> str:
    """'loads[1].pickup_date' -> 'loads[1].pickupDate'; 'config.x_y' -> 'truckSettings.advanced.xY'."""
    if path.startswith("config."):
        path = "truck_settings.advanced." + path.removeprefix("config.")
    return re.sub(r"[a-z0-9]+(?:_[a-z0-9]+)+", lambda m: to_camel(m.group()), path)


def to_json(value: Any) -> Any:
    """Dataclasses/tuples/dates -> plain JSON values with camelCase keys."""
    if isinstance(value, Issue):
        return {"code": value.code, "field": field_to_json(value.field), "message": value.message}
    if isinstance(value, WhyLine):
        # `line` holds an engine field name, so it gets mapped too.
        return {**{to_camel(f.name): getattr(value, f.name) for f in fields(value)}, "line": to_camel(value.line)}
    if is_dataclass(value) and not isinstance(value, type):
        return {to_camel(f.name): to_json(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, (list, tuple)):
        return [to_json(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    return value


# ---------- request parsing ----------


class _Reader:
    """Reads typed values out of a JSON object and collects errors with JSON field paths."""

    def __init__(self, errors: list[Issue]):
        self.errors = errors

    def _err(self, path: str, message: str) -> None:
        self.errors.append(Issue("error", "invalid", path, message))

    def obj(self, parent: dict, key: str, path: str, required: bool = True) -> dict:
        value = parent.get(key)
        if value is None and not required:
            return {}
        if not isinstance(value, dict):
            self._err(path, "Must be an object.")
            return {}
        return value

    def num(self, parent: dict, key: str, path: str, default: Any = None, required: bool = False) -> Any:
        value = parent.get(key)
        if value is None:
            if required:
                self._err(path, "Required.")
            return default
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            self._err(path, "Must be a number.")
            return default
        return float(value)

    def text(self, parent: dict, key: str, path: str, default: str = "") -> str:
        value = parent.get(key)
        if value is None:
            return default
        if not isinstance(value, str):
            self._err(path, "Must be text.")
            return default
        return value.strip()

    def day(self, parent: dict, key: str, path: str, required: bool = False) -> date | None:
        value = parent.get(key)
        if value in (None, ""):
            if required:
                self._err(path, "Required.")
            return None
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            self._err(path, "Must be a date like 2026-10-06.")
            return None


@dataclass(frozen=True)
class RankRequest:
    trip: TripContext
    truck: TruckSettings
    loads: list[LoadInput]
    config: EngineConfig
    diesel_source: str  # "manual" | "eia" | "fallback"


def parse_rank_request(
    body: Any, lookup_diesel: Callable[[str], float | None]
) -> tuple[RankRequest | None, list[Issue]]:
    """Parse a /rank body. lookup_diesel(region) returns the cached EIA price or None.

    Returns (request, []) on success, or (None, errors) with JSON field paths.
    """
    errors: list[Issue] = []
    r = _Reader(errors)
    if not isinstance(body, dict):
        return None, [Issue("error", "invalid", "", "Body must be a JSON object.")]

    t = r.obj(body, "tripContext", "tripContext")
    s = r.obj(body, "truckSettings", "truckSettings")
    adv = r.obj(s, "advanced", "truckSettings.advanced", required=False)
    raw_loads = body.get("loads")
    if not isinstance(raw_loads, list) or len(raw_loads) > MAX_LOADS_IN_REQUEST:
        errors.append(Issue("error", "invalid", "loads", "Must be a list of up to 3 loads."))
        raw_loads = []

    config = replace(
        DEFAULTS,
        **{
            snake: value
            for camel, snake in _ADVANCED.items()
            if (value := r.num(adv, camel, f"truckSettings.advanced.{camel}")) is not None
        },
    )

    trip = TripContext(
        available_date=r.day(t, "availableDate", "tripContext.availableDate", required=True) or date.min,
        cycle_hours_remaining=r.num(t, "cycleHoursRemaining", "tripContext.cycleHoursRemaining"),
        current_location=r.text(t, "currentLocation", "tripContext.currentLocation"),
    )

    region = r.text(s, "fuelRegion", "truckSettings.fuelRegion", DEFAULTS.default_fuel_region)
    if not is_known_region(region):
        errors.append(Issue("error", "invalid", "truckSettings.fuelRegion", f"Unknown fuel region: {region}"))
    diesel = r.num(s, "dieselPrice", "truckSettings.dieselPrice")
    if diesel is not None:
        diesel_source = "manual"
    elif (diesel := lookup_diesel(region)) is not None:
        diesel_source = "eia"
    else:
        diesel, diesel_source = DEFAULTS.fallback_diesel_price, "fallback"

    rounding = r.text(s, "daysRoundingMode", "truckSettings.daysRoundingMode", "fractional")
    truck = TruckSettings(
        diesel_price=diesel,
        monthly_fixed_costs=r.num(s, "monthlyFixedCosts", "truckSettings.monthlyFixedCosts"),
        mpg=r.num(s, "mpg", "truckSettings.mpg", DEFAULTS.default_mpg),
        maintenance_cpm=r.num(s, "maintenanceCpm", "truckSettings.maintenanceCpm", DEFAULTS.default_maintenance_cpm),
        tires_cpm=r.num(s, "tiresCpm", "truckSettings.tiresCpm", DEFAULTS.default_tires_cpm),
        other_cpm=r.num(s, "otherCpm", "truckSettings.otherCpm", DEFAULTS.default_other_cpm),
        payout_percent=r.num(s, "payoutPercent", "truckSettings.payoutPercent", DEFAULTS.default_payout_percent),
        days_rounding_mode=rounding,
        target_profit_per_day=r.num(s, "targetProfitPerDay", "truckSettings.targetProfitPerDay"),
        fuel_region=region,
    )

    loads = []
    for i, raw in enumerate(raw_loads):
        p = f"loads[{i}]"
        if not isinstance(raw, dict):
            errors.append(Issue("error", "invalid", p, "Must be an object."))
            continue
        loads.append(
            LoadInput(
                label=r.text(raw, "label", f"{p}.label") or "ABCDEFGHIJ"[i],
                nickname=r.text(raw, "nickname", f"{p}.nickname"),
                posted_rate=r.num(raw, "postedRate", f"{p}.postedRate", 0.0, required=True),
                loaded_miles=r.num(raw, "loadedMiles", f"{p}.loadedMiles", 0.0, required=True),
                deadhead_miles=r.num(raw, "deadheadMiles", f"{p}.deadheadMiles", 0.0, required=True),
                pickup_location=r.text(raw, "pickupLocation", f"{p}.pickupLocation"),
                dropoff_location=r.text(raw, "dropoffLocation", f"{p}.dropoffLocation"),
                pickup_date=r.day(raw, "pickupDate", f"{p}.pickupDate"),
                delivery_date=r.day(raw, "deliveryDate", f"{p}.deliveryDate"),
                dock_wait_hours=r.num(raw, "dockWaitHours", f"{p}.dockWaitHours"),
                tolls=r.num(raw, "tolls", f"{p}.tolls", 0.0),
            )
        )

    if errors:
        return None, errors
    return RankRequest(trip, truck, loads, config, diesel_source), []


def ranking_to_json(ranking: Ranking, request: RankRequest | None = None) -> dict:
    body = to_json(ranking)
    if request is not None:
        body["diesel"] = {"price": request.truck.diesel_price, "source": request.diesel_source}
    return body
