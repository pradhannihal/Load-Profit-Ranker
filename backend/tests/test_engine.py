"""docs/formula.md §6 worked examples. Money ±$0.01, days ±0.0001."""

from dataclasses import replace

import pytest

from core.engine import compute_load, rank_loads, why_it_won

MONEY = 0.01
DAYS = 0.0001


def by_label(ranking):
    return {r.label: r for r in ranking.results}


class TestFractional:
    """The main worked example."""

    @pytest.fixture
    def results(self, trip, truck, loads):
        return by_label(rank_loads(trip, truck, loads))

    @pytest.mark.parametrize(
        "label, total_miles, drive_hours, duty_hours, hos_days",
        [
            ("A", 665, 13.3, 17.3, 1.2357),
            ("B", 1200, 24.0, 28.0, 2.1818),
            ("C", 540, 10.8, 13.8, 0.9857),
        ],
    )
    def test_time(self, results, label, total_miles, drive_hours, duty_hours, hos_days):
        r = results[label]
        assert r.total_miles == pytest.approx(total_miles)
        assert r.drive_hours == pytest.approx(drive_hours)
        assert r.duty_hours == pytest.approx(duty_hours)
        assert r.hos_days == pytest.approx(hos_days, abs=DAYS)

    @pytest.mark.parametrize(
        "label, days_used, bound_by",
        [("A", 1.2357, "hos"), ("B", 2.1818, "hos"), ("C", 3.0, "schedule")],
    )
    def test_days_used(self, results, label, days_used, bound_by):
        assert results[label].days_used == pytest.approx(days_used, abs=DAYS)
        assert results[label].days_bound_by == bound_by

    @pytest.mark.parametrize(
        "label, revenue, fuel, per_mile, tolls, fixed",
        [
            ("A", 2400.00, 652.72, 176.225, 0.00, 205.95),
            ("B", 3000.00, 1177.85, 318.00, 35.00, 363.64),
            ("C", 1900.00, 530.03, 143.10, 0.00, 500.00),
        ],
    )
    def test_lines(self, results, label, revenue, fuel, per_mile, tolls, fixed):
        lines = results[label].lines
        assert lines.gross_revenue == pytest.approx(revenue, abs=MONEY)
        assert lines.fuel_cost == pytest.approx(fuel, abs=MONEY)
        assert lines.per_mile_cost == pytest.approx(per_mile, abs=MONEY)
        assert lines.tolls == pytest.approx(tolls, abs=MONEY)
        assert lines.fixed_cost == pytest.approx(fixed, abs=MONEY)

    @pytest.mark.parametrize(
        "label, net, per_day, per_mile, board",
        [
            ("A", 1365.10, 1104.70, 2.0528, 3.6923),
            ("B", 1105.52, 506.70, 0.9213, 3.0000),
            ("C", 726.87, 242.29, 1.3461, 3.8000),
        ],
    )
    def test_profit(self, results, label, net, per_day, per_mile, board):
        r = results[label]
        assert r.net_profit == pytest.approx(net, abs=MONEY)
        assert r.profit_per_day == pytest.approx(per_day, abs=MONEY)
        assert r.profit_per_mile == pytest.approx(per_mile, abs=0.0001)
        assert r.board_rate == pytest.approx(board, abs=0.0001)
        assert r.meets_target is None
        assert r.loses_money is False
        assert r.restart_needed is False
        assert r.warnings == ()

    def test_ranking(self, trip, truck, loads):
        ranking = rank_loads(trip, truck, loads)
        assert ranking.ranked
        assert [r.label for r in ranking.results] == ["A", "B", "C"]
        assert [r.rank for r in ranking.results] == [1, 2, 3]
        assert ranking.winner == "A"
        assert ranking.errors == ()

    def test_c_has_best_board_rate_but_ranks_last(self, results):
        assert results["C"].board_rate > results["A"].board_rate > results["B"].board_rate
        assert results["C"].profit_per_day < results["B"].profit_per_day


class TestWhole:
    @pytest.mark.parametrize(
        "label, days_used, net, per_day",
        [
            ("A", 2, 1237.72, 618.86),
            ("B", 3, 969.15, 323.05),
            ("C", 3, 726.87, 242.29),
        ],
    )
    def test_values(self, trip, whole, loads, label, days_used, net, per_day):
        r = by_label(rank_loads(trip, whole, loads))[label]
        assert r.days_used == pytest.approx(days_used, abs=DAYS)
        assert r.net_profit == pytest.approx(net, abs=MONEY)
        assert r.profit_per_day == pytest.approx(per_day, abs=MONEY)

    def test_same_ranking(self, trip, whole, loads):
        assert [r.label for r in rank_loads(trip, whole, loads).results] == ["A", "B", "C"]

    def test_exact_whole_day_is_not_rounded_up(self, trip, whole, loads):
        # 22 drive hours / 11 = exactly 2 days, and the duty limit is lower. Must stay 2, not 3.
        load = replace(loads[0], deadhead_miles=0, loaded_miles=1100, dock_wait_hours=0, delivery_date=None)
        assert compute_load(trip, whole, load).days_used == 2


class TestCycleLimit:
    """cycleHoursRemaining = 20: B needs a 34-hr restart and drops below C."""

    @pytest.mark.parametrize(
        "label, restart, hos_days, fixed, net, per_day, per_mile",
        [
            ("A", False, 1.2357, 205.95, 1365.10, 1104.70, 2.0528),
            ("B", True, 3.5985, 599.75, 869.41, 241.60, 0.7245),
            ("C", False, 0.9857, 500.00, 726.87, 242.29, 1.3461),
        ],
    )
    def test_values(self, low_cycle, truck, loads, label, restart, hos_days, fixed, net, per_day, per_mile):
        r = by_label(rank_loads(low_cycle, truck, loads))[label]
        assert r.restart_needed is restart
        assert r.hos_days == pytest.approx(hos_days, abs=DAYS)
        assert r.lines.fixed_cost == pytest.approx(fixed, abs=MONEY)
        assert r.net_profit == pytest.approx(net, abs=MONEY)
        assert r.profit_per_day == pytest.approx(per_day, abs=MONEY)
        assert r.profit_per_mile == pytest.approx(per_mile, abs=0.0001)

    def test_b_drops_below_c(self, low_cycle, truck, loads):
        ranking = rank_loads(low_cycle, truck, loads)
        assert [r.label for r in ranking.results] == ["A", "C", "B"]

    def test_restart_warning(self, low_cycle, truck, loads):
        results = by_label(rank_loads(low_cycle, truck, loads))
        assert [w.code for w in results["B"].warnings] == ["restart_needed"]
        assert results["B"].restart_days == pytest.approx(34 / 24)
        assert results["A"].restart_days == 0

    def test_whole_mode(self, low_cycle, whole, loads):
        ranking = rank_loads(low_cycle, whole, loads)
        results = by_label(ranking)
        for label, days, net, per_day in [
            ("A", 2, 1237.72, 618.86),
            ("B", 4, 802.49, 200.62),
            ("C", 3, 726.87, 242.29),
        ]:
            assert results[label].days_used == pytest.approx(days, abs=DAYS)
            assert results[label].net_profit == pytest.approx(net, abs=MONEY)
            assert results[label].profit_per_day == pytest.approx(per_day, abs=MONEY)
        assert [r.label for r in ranking.results] == ["A", "C", "B"]


class TestTarget:
    def test_target_600(self, trip, truck, loads):
        results = by_label(rank_loads(trip, replace(truck, target_profit_per_day=600), loads))
        assert results["A"].meets_target is True
        assert results["B"].meets_target is False
        assert results["C"].meets_target is False

    def test_no_target_is_none(self, trip, truck, loads):
        assert all(r.meets_target is None for r in rank_loads(trip, truck, loads).results)


class TestRankingEdges:
    def test_single_load_is_computed_not_ranked(self, trip, truck, loads):
        ranking = rank_loads(trip, truck, loads[:1])
        assert not ranking.ranked
        assert ranking.winner is None
        assert ranking.results[0].rank is None
        assert ranking.results[0].profit_per_day == pytest.approx(1104.70, abs=MONEY)

    def test_losing_load_is_flagged_and_still_ranked(self, trip, truck, loads):
        cheap = replace(loads[1], posted_rate=1000)
        ranking = rank_loads(trip, truck, [loads[0], cheap])
        assert [r.label for r in ranking.results] == ["A", "B"]
        assert ranking.results[1].loses_money is True
        assert ranking.results[1].net_profit < 0

    def test_tie_breaker_is_profit_per_mile(self, trip, truck, loads):
        # Round numbers so both loads tie exactly on profit/day: $1/mi variable cost, $100/day fixed.
        simple = replace(truck, mpg=5, diesel_price=5, maintenance_cpm=0, tires_cpm=0, monthly_fixed_costs=3000)
        x = replace(loads[2], label="X", posted_rate=2000, loaded_miles=500, deadhead_miles=0)
        y = replace(loads[2], label="Y", posted_rate=1900, loaded_miles=400, deadhead_miles=0)
        ranking = rank_loads(trip, simple, [x, y])
        assert [r.profit_per_day for r in ranking.results] == [400, 400]
        assert ranking.winner == "Y"  # $3.00/mi beats $2.40/mi

    def test_exact_tie_keeps_input_order(self, trip, truck, loads):
        ranking = rank_loads(trip, truck, [replace(loads[0], label="P"), replace(loads[0], label="Q")])
        assert [r.label for r in ranking.results] == ["P", "Q"]

    def test_payout_percent(self, trip, truck, loads):
        r = compute_load(trip, replace(truck, payout_percent=75), loads[0])
        assert r.lines.gross_revenue == pytest.approx(1800)
        assert r.board_rate == pytest.approx(2400 / 650)  # board rate uses the posted rate

    def test_default_dock_wait(self, trip, truck, loads):
        r = compute_load(trip, truck, replace(loads[0], dock_wait_hours=None))
        assert r.duty_hours == pytest.approx(17.3)  # 13.3 drive + 2 default wait + 2 buffer


class TestWhyItWon:
    def test_a_over_b(self, trip, truck, loads):
        ranking = rank_loads(trip, truck, loads)
        why = ranking.why_it_won
        # Per day: A earns $1,942.20 vs B $1,375.00, and B pays $16.04/day in tolls.
        assert [w.line for w in why] == ["gross_revenue", "tolls"]
        assert why[0].advantage_per_day == pytest.approx(2400 / 1.235714 - 3000 / 2.181818, abs=MONEY)
        assert why[1].advantage_per_day == pytest.approx(35 / 2.181818, abs=MONEY)

    def test_only_lines_favoring_the_winner(self, trip, truck, loads):
        results = by_label(rank_loads(trip, truck, loads))
        why = why_it_won(results["A"], results["C"], top=5)
        assert all(w.advantage_per_day > 0 for w in why)

    def test_fixed_cost_per_day_never_explains_a_win(self, trip, truck, loads):
        # Fixed $/day = monthly / working days for every load, so it can't separate them.
        results = by_label(rank_loads(trip, truck, loads))
        why = why_it_won(results["A"], results["C"], top=5)
        assert "fixed_cost" not in [w.line for w in why]
