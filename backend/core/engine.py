"""The profit-per-day math (docs/formula.md §2, §4).

Pure functions: numbers in, results out. No clock, no network.
Full float precision everywhere; round only for display.
"""

import math
from dataclasses import fields, replace

from core.config import DEFAULTS, EngineConfig
from core.models import Issue, LineItems, LoadInput, LoadResult, Ranking, TripContext, TruckSettings, WhyLine
from core.validation import validate

# Lines that make up net profit. Revenue counts for the load; the rest count against it.
_REVENUE_LINE = "gross_revenue"
_LINES = tuple(f.name for f in fields(LineItems))


def compute_load(
    trip: TripContext,
    truck: TruckSettings,
    load: LoadInput,
    config: EngineConfig = DEFAULTS,
    warnings: tuple[Issue, ...] = (),
) -> LoadResult:
    """Compute one load. Assumes the inputs already passed validate()."""
    # 1. Miles
    total_miles = load.deadhead_miles + load.loaded_miles

    # 2. HOS time
    dock_wait = config.default_dock_wait_hours if load.dock_wait_hours is None else load.dock_wait_hours
    drive_hours = total_miles / config.avg_speed_mph
    duty_hours = drive_hours + dock_wait + config.buffer_hours
    hos_days = max(drive_hours / config.max_drive_hours, duty_hours / config.max_duty_hours)

    cycle_left = config.max_cycle_hours if trip.cycle_hours_remaining is None else trip.cycle_hours_remaining
    restart_needed = duty_hours > cycle_left
    if restart_needed:
        hos_days += config.restart_hours / 24
        warnings = (
            *warnings,
            Issue("warning", "restart_needed", "trip_context.cycle_hours_remaining", "Needs a 34-hr restart."),
        )

    if truck.days_rounding_mode == "whole":
        # round() first so float noise like 2.0000000001 doesn't become 3 days.
        hos_days = math.ceil(round(hos_days, 9))

    # 3. Schedule time
    schedule_days = (load.delivery_date - trip.available_date).days if load.delivery_date else 0

    # 4. Days used
    if schedule_days > hos_days:
        days_used, days_bound_by = float(schedule_days), "schedule"
    else:
        days_used, days_bound_by = float(hos_days), "hos"

    # 5-7. Revenue and costs
    lines = LineItems(
        gross_revenue=load.posted_rate * truck.payout_percent / 100,
        fuel_cost=total_miles / truck.mpg * truck.diesel_price,
        per_mile_cost=total_miles * (truck.maintenance_cpm + truck.tires_cpm + truck.other_cpm),
        tolls=load.tolls,
        fixed_cost=truck.monthly_fixed_costs / config.working_days_per_month * days_used,
    )
    variable_cost = lines.fuel_cost + lines.per_mile_cost + lines.tolls

    # 8-9. Net, per day, target
    net_profit = lines.gross_revenue - variable_cost - lines.fixed_cost
    profit_per_day = net_profit / days_used
    target = truck.target_profit_per_day
    meets_target = None if target is None else profit_per_day >= target

    return LoadResult(
        label=load.label,
        nickname=load.nickname,
        total_miles=total_miles,
        drive_hours=drive_hours,
        duty_hours=duty_hours,
        restart_needed=restart_needed,
        hos_days=float(hos_days),
        schedule_days=schedule_days,
        days_used=days_used,
        days_bound_by=days_bound_by,
        lines=lines,
        variable_cost=variable_cost,
        net_profit=net_profit,
        profit_per_day=profit_per_day,
        profit_per_mile=net_profit / total_miles,
        board_rate=load.posted_rate / load.loaded_miles,
        meets_target=meets_target,
        loses_money=net_profit < 0,
        warnings=warnings,
    )


def why_it_won(winner: LoadResult, runner_up: LoadResult, top: int = 2) -> tuple[WhyLine, ...]:
    """The lines where the winner's per-day advantage is largest (formula §4 step 12).

    Per day, not raw dollars, so the explanation agrees with the ranking.
    """
    why = []
    for line in _LINES:
        w = getattr(winner.lines, line) / winner.days_used
        r = getattr(runner_up.lines, line) / runner_up.days_used
        advantage = w - r if line == _REVENUE_LINE else r - w
        if advantage > 0:
            why.append(WhyLine(line, w, r, advantage))
    why.sort(key=lambda x: x.advantage_per_day, reverse=True)
    return tuple(why[:top])


def rank_loads(
    trip: TripContext, truck: TruckSettings, loads: list[LoadInput], config: EngineConfig = DEFAULTS
) -> Ranking:
    """Validate, compute, and rank up to 3 loads by profit per day (formula §4 step 11)."""
    errors, warnings_per_load = validate(trip, truck, loads, config)
    if errors:
        return Ranking(errors=tuple(errors))

    results = [
        compute_load(trip, truck, load, config, tuple(warnings))
        for load, warnings in zip(loads, warnings_per_load, strict=True)
    ]
    if len(results) < 2:
        return Ranking(results=tuple(results))

    # Stable sort: exact ties on both keys keep the order Dad entered them.
    results.sort(key=lambda r: (r.profit_per_day, r.profit_per_mile), reverse=True)
    results = [replace(r, rank=i) for i, r in enumerate(results, start=1)]
    return Ranking(
        results=tuple(results),
        ranked=True,
        winner=results[0].label,
        why_it_won=why_it_won(results[0], results[1]),
    )
