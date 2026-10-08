"""Input checks (docs/formula.md §5).

Errors block results. Warnings are attached to a load, and it is still ranked.
The "needs a 34-hr restart" warning depends on computed duty hours, so the
engine adds it, not this module.
"""

from core.config import EngineConfig
from core.models import Issue, LoadInput, TripContext, TruckSettings

MAX_LOADS = 3


def _error(code: str, field: str, message: str) -> Issue:
    return Issue("error", code, field, message)


def _check_config(config: EngineConfig) -> list[Issue]:
    # These are user-editable under Settings > Advanced, and the math divides by them.
    errors = []
    positive = {
        "avg_speed_mph": "Average speed",
        "max_drive_hours": "Max driving hours",
        "max_duty_hours": "Max duty hours",
        "max_cycle_hours": "Cycle hours",
        "working_days_per_month": "Working days per month",
    }
    for name, label in positive.items():
        if getattr(config, name) <= 0:
            errors.append(_error("must_be_positive", f"config.{name}", f"{label} must be more than 0."))
    if config.working_days_per_month > 31:
        errors.append(
            _error("too_many_days", "config.working_days_per_month", "Working days per month can't be more than 31.")
        )
    if config.buffer_hours < 0:
        errors.append(_error("negative", "config.buffer_hours", "Buffer hours can't be negative."))
    if config.restart_hours < 0:
        errors.append(_error("negative", "config.restart_hours", "Restart hours can't be negative."))
    return errors


def _check_settings(truck: TruckSettings) -> list[Issue]:
    errors = []
    f = "truck_settings"
    if truck.mpg <= 0:
        errors.append(_error("must_be_positive", f"{f}.mpg", "MPG must be more than 0."))
    if truck.diesel_price <= 0:
        errors.append(_error("must_be_positive", f"{f}.diesel_price", "Diesel price must be more than 0."))
    if truck.monthly_fixed_costs is None or truck.monthly_fixed_costs <= 0:
        errors.append(
            _error(
                "fixed_costs_missing",
                f"{f}.monthly_fixed_costs",
                "Enter your monthly fixed costs in Settings. Profit per day means nothing without them.",
            )
        )
    for name in ("maintenance_cpm", "tires_cpm", "other_cpm"):
        if getattr(truck, name) < 0:
            errors.append(_error("negative", f"{f}.{name}", "Per-mile costs can't be negative."))
    if not 1 <= truck.payout_percent <= 100:
        errors.append(_error("out_of_range", f"{f}.payout_percent", "Payout must be between 1% and 100%."))
    if truck.days_rounding_mode not in ("fractional", "whole"):
        errors.append(_error("invalid", f"{f}.days_rounding_mode", "Rounding must be 'fractional' or 'whole'."))
    if truck.target_profit_per_day is not None and truck.target_profit_per_day < 0:
        errors.append(_error("negative", f"{f}.target_profit_per_day", "Target profit per day can't be negative."))
    return errors


def _check_trip(trip: TripContext, config: EngineConfig) -> list[Issue]:
    c = trip.cycle_hours_remaining
    if c is not None and not 0 <= c <= config.max_cycle_hours:
        return [
            _error(
                "out_of_range",
                "trip_context.cycle_hours_remaining",
                f"Cycle hours left must be between 0 and {config.max_cycle_hours:g}.",
            )
        ]
    return []


def _check_load(
    i: int, load: LoadInput, trip: TripContext, config: EngineConfig, check_pickup: bool
) -> tuple[list[Issue], list[Issue]]:
    errors, warnings = [], []
    f = f"loads[{i}]"
    if load.loaded_miles <= 0:
        errors.append(_error("must_be_positive", f"{f}.loaded_miles", "Loaded miles must be more than 0."))
    if load.deadhead_miles < 0:
        errors.append(_error("negative", f"{f}.deadhead_miles", "Deadhead miles can't be negative."))
    if load.posted_rate < 0:
        errors.append(_error("negative", f"{f}.posted_rate", "Rate can't be negative."))
    if load.tolls < 0:
        errors.append(_error("negative", f"{f}.tolls", "Tolls can't be negative."))
    if load.dock_wait_hours is not None and load.dock_wait_hours < 0:
        errors.append(_error("negative", f"{f}.dock_wait_hours", "Dock wait can't be negative."))
    if load.delivery_date is not None and load.delivery_date < trip.available_date:
        errors.append(
            _error("delivery_before_available", f"{f}.delivery_date", "Delivery date is before the truck is available.")
        )
    if load.pickup_date is not None and load.delivery_date is not None and load.pickup_date > load.delivery_date:
        errors.append(_error("pickup_after_delivery", f"{f}.pickup_date", "Pickup date is after the delivery date."))

    if check_pickup and load.pickup_date is not None and load.deadhead_miles >= 0:
        days_to_pickup = (load.pickup_date - trip.available_date).days
        too_early = days_to_pickup < 0
        too_far = (load.deadhead_miles / config.avg_speed_mph) > config.max_drive_hours * (days_to_pickup + 1)
        if too_early or too_far:
            warnings.append(Issue("warning", "pickup_at_risk", f"{f}.pickup_date", "May not make this pickup in time."))
    return errors, warnings


def validate(
    trip: TripContext, truck: TruckSettings, loads: list[LoadInput], config: EngineConfig
) -> tuple[list[Issue], list[list[Issue]]]:
    """Return (errors, warnings per load). Results are valid only if errors is empty."""
    config_errors = _check_config(config)
    errors = config_errors + _check_settings(truck) + _check_trip(trip, config)
    if not loads:
        errors.append(_error("no_loads", "loads", "Add at least one load."))
    if len(loads) > MAX_LOADS:
        errors.append(_error("too_many_loads", "loads", f"Compare at most {MAX_LOADS} loads."))

    warnings_per_load: list[list[Issue]] = []
    for i, load in enumerate(loads):
        # The pickup check divides by avg speed, so skip it when the config is bad.
        load_errors, load_warnings = _check_load(i, load, trip, config, check_pickup=not config_errors)
        errors += load_errors
        warnings_per_load.append(load_warnings)
    return errors, warnings_per_load
