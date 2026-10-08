"""The local Flask API, end to end with a fake fuel cache. Also covers handlers/mapping.py."""

import pytest

from handlers.mapping import field_to_json, to_camel
from local.app import create_app

WORKED_EXAMPLE = {
    "tripContext": {"availableDate": "2026-10-06", "currentLocation": "Richmond, VA"},
    "truckSettings": {"dieselPrice": 6.38, "monthlyFixedCosts": 5000},
    "loads": [
        {"label": "A", "postedRate": 2400, "deadheadMiles": 15, "loadedMiles": 650, "dockWaitHours": 2,
         "deliveryDate": "2026-10-07"},
        {"label": "B", "postedRate": 3000, "deadheadMiles": 200, "loadedMiles": 1000, "dockWaitHours": 2,
         "tolls": 35, "deliveryDate": "2026-10-08"},
        {"label": "C", "postedRate": 1900, "deadheadMiles": 40, "loadedMiles": 500, "dockWaitHours": 1,
         "deliveryDate": "2026-10-09"},
    ],
}  # fmt: skip


class FakeFuel:
    def __init__(self, price=5.699):
        self.price = price

    def get(self, region):
        return {"region": region, "price": self.price, "asOf": "2026-10-05", "source": "eia", "stale": False}

    def cached_price(self, region):
        return self.price


@pytest.fixture
def client():
    return create_app(fuel_cache=FakeFuel()).test_client()


def body_with(**changes):
    import copy

    body = copy.deepcopy(WORKED_EXAMPLE)
    for path, value in changes.items():
        section, key = path.split("__")
        body[section][key] = value
    return body


class TestRank:
    def test_worked_example(self, client):
        resp = client.post("/api/rank", json=WORKED_EXAMPLE)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ranked"] is True
        assert data["winner"] == "A"
        assert [r["label"] for r in data["results"]] == ["A", "B", "C"]
        a = data["results"][0]
        assert a["profitPerDay"] == pytest.approx(1104.70, abs=0.01)
        assert a["daysBoundBy"] == "hos"
        assert a["lines"]["fuelCost"] == pytest.approx(652.72, abs=0.01)
        assert data["results"][2]["daysBoundBy"] == "schedule"
        assert data["whyItWon"][0]["line"] == "grossRevenue"
        assert data["diesel"] == {"price": 6.38, "source": "manual"}
        assert data["errors"] == []

    def test_uses_cached_eia_price_without_override(self, client):
        body = body_with(truckSettings__dieselPrice=None)
        data = client.post("/api/rank", json=body).get_json()
        assert data["diesel"] == {"price": 5.699, "source": "eia"}

    def test_fallback_price_when_nothing_cached(self):
        client = create_app(fuel_cache=FakeFuel(price=None)).test_client()
        data = client.post("/api/rank", json=body_with(truckSettings__dieselPrice=None)).get_json()
        assert data["diesel"] == {"price": 6.38, "source": "fallback"}

    def test_cycle_limit_flips_b_below_c(self, client):
        data = client.post("/api/rank", json=body_with(tripContext__cycleHoursRemaining=20)).get_json()
        assert [r["label"] for r in data["results"]] == ["A", "C", "B"]
        b = data["results"][2]
        assert b["warnings"] == [
            {"code": "restart_needed", "field": "tripContext.cycleHoursRemaining", "message": "Needs a 34-hr restart."}
        ]

    def test_advanced_settings_reach_the_engine(self, client):
        body = body_with(truckSettings__advanced={"workingDaysPerMonth": 20})
        a = client.post("/api/rank", json=body).get_json()["results"][0]
        assert a["lines"]["fixedCost"] == pytest.approx(5000 / 20 * 1.235714, abs=0.01)

    def test_validation_error_uses_json_field_names(self, client):
        body = body_with(truckSettings__monthlyFixedCosts=None)
        resp = client.post("/api/rank", json=body)
        assert resp.status_code == 422
        err = resp.get_json()["errors"][0]
        assert err["code"] == "fixed_costs_missing"
        assert err["field"] == "truckSettings.monthlyFixedCosts"

    def test_engine_load_error_path(self, client):
        body = body_with()
        body["loads"][1]["loadedMiles"] = 0
        fields = [e["field"] for e in client.post("/api/rank", json=body).get_json()["errors"]]
        assert "loads[1].loadedMiles" in fields

    def test_advanced_error_path(self, client):
        body = body_with(truckSettings__advanced={"avgSpeedMph": 0})
        fields = [e["field"] for e in client.post("/api/rank", json=body).get_json()["errors"]]
        assert "truckSettings.advanced.avgSpeedMph" in fields

    @pytest.mark.parametrize(
        "mutate, field",
        [
            (lambda b: b["loads"][0].update(postedRate="2400"), "loads[0].postedRate"),
            (lambda b: b["loads"][0].pop("loadedMiles"), "loads[0].loadedMiles"),
            (lambda b: b["loads"][0].update(deliveryDate="10/07/2026"), "loads[0].deliveryDate"),
            (lambda b: b["tripContext"].pop("availableDate"), "tripContext.availableDate"),
            (lambda b: b["truckSettings"].update(mpg=True), "truckSettings.mpg"),
            (lambda b: b["truckSettings"].update(fuelRegion="MARS"), "truckSettings.fuelRegion"),
            (lambda b: b.update(loads="nope"), "loads"),
        ],
    )
    def test_bad_types(self, client, mutate, field):
        body = body_with()
        mutate(body)
        resp = client.post("/api/rank", json=body)
        assert resp.status_code == 422
        assert field in [e["field"] for e in resp.get_json()["errors"]]

    def test_not_json(self, client):
        resp = client.post("/api/rank", data="hello", content_type="text/plain")
        assert resp.status_code == 422

    def test_single_load(self, client):
        body = body_with()
        body["loads"] = body["loads"][:1]
        data = client.post("/api/rank", json=body).get_json()
        assert data["ranked"] is False
        assert data["results"][0]["rank"] is None


class TestFuel:
    def test_fuel(self, client):
        data = client.get("/api/fuel?region=R1Z").get_json()
        assert data["price"] == 5.699
        assert data["asOf"] == "2026-10-05"

    def test_unknown_region(self, client):
        assert client.get("/api/fuel?region=XX").status_code == 422

    def test_regions(self, client):
        codes = [r["code"] for r in client.get("/api/regions").get_json()]
        assert "R1Z" in codes


def test_name_mapping():
    assert to_camel("profit_per_day") == "profitPerDay"
    assert field_to_json("loads[1].pickup_date") == "loads[1].pickupDate"
    assert field_to_json("truck_settings.mpg") == "truckSettings.mpg"
    assert field_to_json("config.working_days_per_month") == "truckSettings.advanced.workingDaysPerMonth"
