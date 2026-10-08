from dataclasses import FrozenInstanceError, replace

import pytest

from core.config import DEFAULTS, EngineConfig


def test_defaults_match_formula():
    c = EngineConfig()
    assert (c.avg_speed_mph, c.max_drive_hours, c.max_duty_hours) == (50, 11, 14)
    assert (c.max_cycle_hours, c.restart_hours, c.buffer_hours) == (70, 34, 2)
    assert c.working_days_per_month == 30
    assert (c.default_mpg, c.default_maintenance_cpm, c.default_tires_cpm) == (6.5, 0.215, 0.050)
    assert c.fallback_diesel_price == 6.38
    assert c.default_fuel_region == "R1Z"


def test_frozen():
    with pytest.raises(FrozenInstanceError):
        DEFAULTS.avg_speed_mph = 60


def test_replace_makes_a_new_config():
    sixty = replace(DEFAULTS, max_cycle_hours=60)
    assert sixty.max_cycle_hours == 60
    assert DEFAULTS.max_cycle_hours == 70
