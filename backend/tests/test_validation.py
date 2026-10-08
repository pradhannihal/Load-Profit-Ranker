"""One test per docs/formula.md §5 row (plus guards for user-editable config)."""

from dataclasses import replace
from datetime import timedelta

import pytest

from core.config import DEFAULTS
from core.engine import rank_loads
from core.validation import validate
from tests.conftest import AVAILABLE


def error_codes(trip, truck, loads, config=DEFAULTS):
    errors, _ = validate(trip, truck, loads, config)
    return {(e.code, e.field) for e in errors}


def test_worked_example_is_valid(trip, truck, loads):
    errors, warnings = validate(trip, truck, loads, DEFAULTS)
    assert errors == []
    assert warnings == [[], [], []]


@pytest.mark.parametrize(
    "change, code, field",
    [
        ({"loaded_miles": 0}, "must_be_positive", "loads[0].loaded_miles"),
        ({"deadhead_miles": -1}, "negative", "loads[0].deadhead_miles"),
        ({"posted_rate": -5}, "negative", "loads[0].posted_rate"),
        ({"tolls": -1}, "negative", "loads[0].tolls"),
        ({"dock_wait_hours": -1}, "negative", "loads[0].dock_wait_hours"),
        ({"delivery_date": AVAILABLE - timedelta(days=1)}, "delivery_before_available", "loads[0].delivery_date"),
        (
            {"pickup_date": AVAILABLE + timedelta(days=2), "delivery_date": AVAILABLE + timedelta(days=1)},
            "pickup_after_delivery",
            "loads[0].pickup_date",
        ),
    ],
)
def test_load_errors(trip, truck, loads, change, code, field):
    bad = [replace(loads[0], **change), *loads[1:]]
    assert (code, field) in error_codes(trip, truck, bad)


@pytest.mark.parametrize(
    "change, code, field",
    [
        ({"mpg": 0}, "must_be_positive", "truck_settings.mpg"),
        ({"diesel_price": 0}, "must_be_positive", "truck_settings.diesel_price"),
        ({"monthly_fixed_costs": None}, "fixed_costs_missing", "truck_settings.monthly_fixed_costs"),
        ({"monthly_fixed_costs": 0}, "fixed_costs_missing", "truck_settings.monthly_fixed_costs"),
        ({"payout_percent": 0}, "out_of_range", "truck_settings.payout_percent"),
        ({"payout_percent": 101}, "out_of_range", "truck_settings.payout_percent"),
        ({"target_profit_per_day": -1}, "negative", "truck_settings.target_profit_per_day"),
        ({"maintenance_cpm": -0.1}, "negative", "truck_settings.maintenance_cpm"),
        ({"days_rounding_mode": "nearest"}, "invalid", "truck_settings.days_rounding_mode"),
    ],
)
def test_settings_errors(trip, truck, loads, change, code, field):
    assert (code, field) in error_codes(trip, replace(truck, **change), loads)


@pytest.mark.parametrize("hours", [-1, 71])
def test_cycle_hours_out_of_range(trip, truck, loads, hours):
    codes = error_codes(replace(trip, cycle_hours_remaining=hours), truck, loads)
    assert ("out_of_range", "trip_context.cycle_hours_remaining") in codes


def test_cycle_hours_limit_follows_config(trip, truck, loads):
    sixty = replace(DEFAULTS, max_cycle_hours=60)
    codes = error_codes(replace(trip, cycle_hours_remaining=65), truck, loads, sixty)
    assert ("out_of_range", "trip_context.cycle_hours_remaining") in codes


@pytest.mark.parametrize("name", ["avg_speed_mph", "working_days_per_month", "max_drive_hours"])
def test_config_must_be_positive(trip, truck, loads, name):
    codes = error_codes(trip, truck, loads, replace(DEFAULTS, **{name: 0}))
    assert ("must_be_positive", f"config.{name}") in codes


def test_bad_config_still_reports_load_errors(trip, truck, loads):
    bad = [replace(loads[0], loaded_miles=0, pickup_date=AVAILABLE)]
    codes = error_codes(trip, truck, bad, replace(DEFAULTS, avg_speed_mph=0))
    assert ("must_be_positive", "loads[0].loaded_miles") in codes


def test_no_loads(trip, truck):
    assert ("no_loads", "loads") in error_codes(trip, truck, [])


def test_too_many_loads(trip, truck, loads):
    assert ("too_many_loads", "loads") in error_codes(trip, truck, [*loads, loads[0]])


def test_errors_block_results(trip, truck, loads):
    ranking = rank_loads(trip, replace(truck, monthly_fixed_costs=None), loads)
    assert ranking.results == ()
    assert not ranking.ranked
    assert ranking.errors[0].code == "fixed_costs_missing"


class TestPickupWarning:
    def warnings(self, trip, truck, load):
        errors, warnings = validate(trip, truck, [load], DEFAULTS)
        assert errors == []
        return [w.code for w in warnings[0]]

    def test_pickup_before_available(self, trip, truck, loads):
        load = replace(loads[0], pickup_date=AVAILABLE - timedelta(days=1), delivery_date=None)
        assert self.warnings(trip, truck, load) == ["pickup_at_risk"]

    def test_deadhead_too_far_for_same_day(self, trip, truck, loads):
        # 600 mi / 50 mph = 12 h > 11 h of driving available today.
        load = replace(loads[0], deadhead_miles=600, pickup_date=AVAILABLE)
        assert self.warnings(trip, truck, load) == ["pickup_at_risk"]

    def test_deadhead_ok_with_an_extra_day(self, trip, truck, loads):
        load = replace(loads[0], deadhead_miles=600, pickup_date=AVAILABLE + timedelta(days=1))
        assert self.warnings(trip, truck, load) == []

    def test_no_pickup_date_no_warning(self, trip, truck, loads):
        assert self.warnings(trip, truck, replace(loads[0], deadhead_miles=5000)) == []

    def test_warning_is_still_ranked(self, trip, truck, loads):
        late = replace(loads[0], pickup_date=AVAILABLE - timedelta(days=1), delivery_date=None)
        ranking = rank_loads(trip, truck, [late, loads[1]])
        assert ranking.ranked
        a = next(r for r in ranking.results if r.label == "A")
        assert [w.code for w in a.warnings] == ["pickup_at_risk"]
