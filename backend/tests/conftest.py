"""Shared fixtures: the docs/formula.md §6 worked example."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from core.models import LoadInput, TripContext, TruckSettings

AVAILABLE = date(2026, 10, 6)


def _delivery(schedule_days: int) -> date:
    return AVAILABLE + timedelta(days=schedule_days)


@pytest.fixture
def trip() -> TripContext:
    return TripContext(available_date=AVAILABLE)


@pytest.fixture
def truck() -> TruckSettings:
    # §6 settings. $5,000 fixed is a placeholder, not Dad's number.
    return TruckSettings(diesel_price=6.38, monthly_fixed_costs=5000)


@pytest.fixture
def loads() -> list[LoadInput]:
    return [
        LoadInput("A", posted_rate=2400, deadhead_miles=15, loaded_miles=650, dock_wait_hours=2, tolls=0,
                  delivery_date=_delivery(1)),
        LoadInput("B", posted_rate=3000, deadhead_miles=200, loaded_miles=1000, dock_wait_hours=2, tolls=35,
                  delivery_date=_delivery(2)),
        LoadInput("C", posted_rate=1900, deadhead_miles=40, loaded_miles=500, dock_wait_hours=1, tolls=0,
                  delivery_date=_delivery(3)),
    ]  # fmt: skip


@pytest.fixture
def whole(truck: TruckSettings) -> TruckSettings:
    return replace(truck, days_rounding_mode="whole")


@pytest.fixture
def low_cycle(trip: TripContext) -> TripContext:
    return replace(trip, cycle_hours_remaining=20)
