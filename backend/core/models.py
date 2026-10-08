"""Inputs and outputs of the engine (docs/formula.md §3, §4 step 10).

Plain frozen dataclasses with snake_case names. The camelCase JSON names
from formula.md are mapped in exactly one place: handlers/mapping.py.
"""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from core.config import DEFAULTS

RoundingMode = Literal["fractional", "whole"]
DaysBoundBy = Literal["hos", "schedule"]
Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class TripContext:
    """Entered once per comparison (formula §3a)."""

    available_date: date  # passed in by the caller; the engine never reads the clock
    cycle_hours_remaining: float | None = None  # None = fresh cycle (config.max_cycle_hours)
    current_location: str = ""  # used by routing in R1.5, not by the math


@dataclass(frozen=True)
class TruckSettings:
    """Set once, editable (formula §3c).

    diesel_price is already resolved by the caller (manual override,
    else latest EIA price, else config.fallback_diesel_price).
    """

    diesel_price: float
    monthly_fixed_costs: float | None  # required; None = not entered yet
    mpg: float = DEFAULTS.default_mpg
    maintenance_cpm: float = DEFAULTS.default_maintenance_cpm
    tires_cpm: float = DEFAULTS.default_tires_cpm
    other_cpm: float = DEFAULTS.default_other_cpm
    payout_percent: float = DEFAULTS.default_payout_percent
    days_rounding_mode: RoundingMode = "fractional"
    target_profit_per_day: float | None = None
    fuel_region: str = DEFAULTS.default_fuel_region


@dataclass(frozen=True)
class LoadInput:
    """One load offer (formula §3b)."""

    label: str  # "A", "B", "C"
    posted_rate: float
    loaded_miles: float
    deadhead_miles: float
    nickname: str = ""
    pickup_location: str = ""
    dropoff_location: str = ""
    pickup_date: date | None = None
    delivery_date: date | None = None
    dock_wait_hours: float | None = None  # None = config.default_dock_wait_hours
    tolls: float = 0.0


@dataclass(frozen=True)
class Issue:
    """A validation error (blocks results) or warning (still ranked)."""

    severity: Severity
    code: str  # stable id for the UI, e.g. "restart_needed"
    field: str  # snake_case path, e.g. "loads[1].pickup_date"
    message: str


@dataclass(frozen=True)
class LineItems:
    """The money lines that make up net profit."""

    gross_revenue: float
    fuel_cost: float
    per_mile_cost: float
    tolls: float
    fixed_cost: float


@dataclass(frozen=True)
class LoadResult:
    label: str
    nickname: str
    total_miles: float
    drive_hours: float
    duty_hours: float
    restart_needed: bool
    restart_days: float  # part of hos_days that is the 34-hr restart (0 if none)
    hos_days: float
    schedule_days: int
    days_used: float
    days_bound_by: DaysBoundBy
    lines: LineItems
    variable_cost: float
    net_profit: float
    profit_per_day: float
    profit_per_mile: float
    board_rate: float  # posted rate per loaded mile, display only
    meets_target: bool | None  # None when no target is set
    loses_money: bool
    warnings: tuple[Issue, ...] = ()
    rank: int | None = None  # None when fewer than 2 loads


@dataclass(frozen=True)
class WhyLine:
    """One line of "why it won", in $ per day of truck time (formula §4 step 12)."""

    line: str  # a LineItems field name
    winner_per_day: float
    runner_up_per_day: float
    advantage_per_day: float  # > 0 means this line favors the winner


@dataclass(frozen=True)
class Ranking:
    results: tuple[LoadResult, ...] = ()  # best first when ranked, else input order
    ranked: bool = False  # False when there are fewer than 2 loads or errors
    winner: str | None = None
    why_it_won: tuple[WhyLine, ...] = ()
    errors: tuple[Issue, ...] = ()
