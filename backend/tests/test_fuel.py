import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import requests

from core.fuel import FuelParseError, is_stale, parse_eia_response
from local.fuel_cache import FuelCache, eia_params

SAMPLE = json.loads((Path(__file__).parent / "data" / "eia_r1z_2026-10-05.json").read_text())
NOW = datetime(2026, 10, 7, 12, tzinfo=UTC)


class TestParse:
    def test_real_response(self):
        fp = parse_eia_response(SAMPLE)
        assert fp.price == pytest.approx(5.699)  # EIA sends it as the string "5.699"
        assert fp.as_of == date(2026, 10, 5)
        assert fp.region == "R1Z"
        assert fp.series == "EMD_EPD2D_PTE_R1Z_DPG"

    def test_picks_newest_row(self):
        older = dict(SAMPLE["response"]["data"][0], period="2026-09-28", value="6.10")
        body = {"response": {"data": [older, SAMPLE["response"]["data"][0]]}}
        assert parse_eia_response(body).as_of == date(2026, 10, 5)

    @pytest.mark.parametrize(
        "body",
        [
            {},
            {"response": {"data": []}},
            {"response": {"data": [{"period": "2026-10-05", "duoarea": "R1Z", "value": "n/a"}]}},
            {"response": {"data": [{"period": "2026-10-05", "duoarea": "R1Z", "value": "0"}]}},
            {"response": {"data": [{"period": "bad", "duoarea": "R1Z", "value": "5.6"}]}},
        ],
    )
    def test_bad_bodies(self, body):
        with pytest.raises(FuelParseError):
            parse_eia_response(body)

    def test_stale(self):
        assert not is_stale(date(2026, 10, 5), date(2026, 10, 15))
        assert is_stale(date(2026, 10, 5), date(2026, 10, 16))


class FakeResponse:
    def __init__(self, body, status=200):
        self.body, self.status = body, status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"{self.status}")

    def json(self):
        return self.body


class FakeFetch:
    def __init__(self, response=None, exc=None):
        self.response, self.exc, self.calls = response, exc, []

    def __call__(self, url, params, timeout):
        self.calls.append(params)
        if self.exc:
            raise self.exc
        return self.response


def make_cache(tmp_path, fetch, api_key="test-key", now=NOW):
    return FuelCache(tmp_path / "fuel.json", api_key, fetch=fetch, now=lambda: now)


class TestCache:
    def test_fetches_and_caches(self, tmp_path):
        fetch = FakeFetch(FakeResponse(SAMPLE))
        cache = make_cache(tmp_path, fetch)
        got = cache.get("R1Z")
        assert got == {"region": "R1Z", "price": 5.699, "asOf": "2026-10-05", "source": "eia", "stale": False}
        assert fetch.calls[0]["facets[duoarea][]"] == "R1Z"
        cache.get("R1Z")
        assert len(fetch.calls) == 1  # second call served from cache
        assert cache.cached_price("R1Z") == 5.699

    def test_refreshes_after_a_day(self, tmp_path):
        fetch = FakeFetch(FakeResponse(SAMPLE))
        make_cache(tmp_path, fetch).get("R1Z")
        make_cache(tmp_path, fetch, now=NOW + timedelta(hours=25)).get("R1Z")
        assert len(fetch.calls) == 2

    def test_eia_down_serves_old_price_as_stale(self, tmp_path):
        make_cache(tmp_path, FakeFetch(FakeResponse(SAMPLE))).get("R1Z")
        later = NOW + timedelta(days=12)
        got = make_cache(tmp_path, FakeFetch(exc=requests.ConnectionError()), now=later).get("R1Z")
        assert got["price"] == 5.699
        assert got["stale"] is True

    def test_no_key_no_cache_uses_fallback(self, tmp_path):
        fetch = FakeFetch(FakeResponse(SAMPLE))
        got = make_cache(tmp_path, fetch, api_key=None).get("R1Z")
        assert got["source"] == "fallback"
        assert got["price"] == 6.38
        assert fetch.calls == []

    def test_http_error_uses_fallback(self, tmp_path):
        got = make_cache(tmp_path, FakeFetch(FakeResponse({}, status=403))).get("R1Z")
        assert got["source"] == "fallback"

    def test_params_ask_for_newest_single_row(self):
        p = eia_params("k", "R1Z")
        assert (p["sort[0][direction]"], p["length"], p["facets[product][]"]) == ("desc", 1, "EPD2D")
