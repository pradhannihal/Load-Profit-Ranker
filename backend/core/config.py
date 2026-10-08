"""Every constant and default the engine uses (docs/formula.md §3c, §3d).

Frozen so a config can't change halfway through ranking a set of loads.
To change a value, build a new one with dataclasses.replace().
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConfig:
    # --- Engine constants (formula §3d) ---
    avg_speed_mph: float = 50.0  # mph, planning estimate incl. stops (not a regulation)
    max_drive_hours: float = 11.0  # h/day, FMCSA 49 CFR 395
    max_duty_hours: float = 14.0  # h/day, FMCSA 49 CFR 395
    max_cycle_hours: float = 70.0  # h, FMCSA 70-hr/8-day (60 for 60/7)
    restart_hours: float = 34.0  # h, FMCSA 34-hour restart
    buffer_hours: float = 2.0  # h per load, ESTIMATE: pre-trip, fueling, load/unload
    working_days_per_month: float = 30.0  # days, PLACEHOLDER until Dad answers §8 Q6

    # --- Defaults for truck settings and loads (formula §3b, §3c) ---
    default_mpg: float = 6.5  # mi/gal, ESTIMATE
    default_maintenance_cpm: float = 0.215  # $/mi, ATRI 2026
    default_tires_cpm: float = 0.050  # $/mi, ATRI 2026
    default_other_cpm: float = 0.0  # $/mi
    default_payout_percent: float = 100.0  # %, 100 = own authority
    default_dock_wait_hours: float = 2.0  # h, ESTIMATE
    default_fuel_region: str = "R1Z"  # EIA duoarea code, PADD 1C (Lower Atlantic)
    fallback_diesel_price: float = 6.38  # $/gal, EIA US avg week of 2026-09-28


DEFAULTS = EngineConfig()
