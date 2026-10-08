"""Local stand-in for the M4 weekly job + DynamoDB: fetch EIA, cache in a JSON file.

Refreshes a region at most once a day. If EIA is down, serves the last cached
price (flagged stale when it's old) or the formula's fallback price.
"""

import json
import logging
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import requests

from core.config import DEFAULTS
from core.fuel import FuelParseError, FuelPrice, is_stale, parse_eia_response

log = logging.getLogger(__name__)

EIA_URL = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
REFRESH_AFTER = timedelta(hours=24)


def eia_params(api_key: str, region: str) -> dict:
    return {
        "api_key": api_key,
        "frequency": "weekly",
        "data[]": "value",
        "facets[duoarea][]": region,
        "facets[product][]": "EPD2D",  # No 2 Diesel, retail on-highway
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 1,
    }


class FuelCache:
    def __init__(
        self,
        path: Path,
        api_key: str | None,
        fetch: Callable[..., requests.Response] = requests.get,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self.path = path
        self.api_key = api_key
        self.fetch = fetch
        self.now = now

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2))

    def _fetch_eia(self, region: str) -> FuelPrice:
        resp = self.fetch(EIA_URL, params=eia_params(self.api_key, region), timeout=10)
        resp.raise_for_status()
        return parse_eia_response(resp.json())

    def get(self, region: str) -> dict:
        """Return {region, price, asOf, source, stale} for the /fuel endpoint."""
        cache = self._load()
        entry = cache.get(region)
        now = self.now()

        fresh = entry and now - datetime.fromisoformat(entry["fetchedAt"]) < REFRESH_AFTER
        if not fresh and self.api_key:
            try:
                fp = self._fetch_eia(region)
                entry = {
                    "price": fp.price,
                    "asOf": fp.as_of.isoformat(),
                    "series": fp.series,
                    "fetchedAt": now.isoformat(),
                }
                cache[region] = entry
                self._save(cache)
            except (requests.RequestException, FuelParseError, ValueError) as e:
                # Never log the request URL: it contains the API key.
                log.warning("EIA fetch failed for %s: %s", region, type(e).__name__)

        today = now.date()
        if entry:
            as_of = date.fromisoformat(entry["asOf"])
            return {
                "region": region,
                "price": entry["price"],
                "asOf": entry["asOf"],
                "source": "eia",
                "stale": is_stale(as_of, today),
            }
        return {
            "region": region,
            "price": DEFAULTS.fallback_diesel_price,
            "asOf": None,
            "source": "fallback",
            "stale": True,
        }

    def cached_price(self, region: str) -> float | None:
        """For /rank: the cached price only, never a network call."""
        entry = self._load().get(region)
        return entry["price"] if entry else None
