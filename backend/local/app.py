"""Local dev API (Flask). Thin adapter: HTTP <-> handlers/mapping.py <-> core/.

Run from backend/:  flask --app local.app run --debug   (Flask finds create_app())
The Vite dev server proxies /api to this port, so the phone only needs Vite.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from core.engine import rank_loads
from core.regions import REGIONS, is_known_region
from handlers.mapping import parse_rank_request, ranking_to_json, to_json
from local.fuel_cache import FuelCache

BACKEND_DIR = Path(__file__).resolve().parent.parent


def create_app(fuel_cache: FuelCache | None = None) -> Flask:
    if fuel_cache is None:
        load_dotenv(BACKEND_DIR / ".env")
        fuel_cache = FuelCache(BACKEND_DIR / ".cache" / "fuel.json", os.environ.get("EIA_API_KEY"))

    app = Flask(__name__)
    app.json.sort_keys = False

    @app.get("/api/regions")
    def regions():
        return jsonify([{"code": code, "name": name} for code, name in REGIONS.items()])

    @app.get("/api/fuel")
    def fuel():
        region = request.args.get("region", "R1Z")
        if not is_known_region(region):
            return jsonify({"errors": [{"code": "invalid", "field": "region", "message": "Unknown region"}]}), 422
        return jsonify(fuel_cache.get(region))

    @app.post("/api/rank")
    def rank():
        parsed, errors = parse_rank_request(request.get_json(silent=True), fuel_cache.cached_price)
        if errors:
            return jsonify({"errors": to_json(errors)}), 422
        ranking = rank_loads(parsed.trip, parsed.truck, parsed.loads, parsed.config)
        status = 422 if ranking.errors else 200
        return jsonify(ranking_to_json(ranking, parsed)), status

    return app
