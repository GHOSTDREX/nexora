"""
AgriNova — Mandi (market) price lookup.

Live daily commodity prices from data.gov.in's Agmarknet dataset ("Current
Daily Price of Various Commodities from Various Markets (Mandi)"), filtered
by the farm's state and crop. Same graceful-degradation shape as the weather
router: cached in-memory (prices update once/day, so a 6h TTL is generous),
and if AGMARKNET_API_KEY isn't set the endpoint says so explicitly rather
than showing fake numbers — mirrors how the AI Assistant degrades to a
rule-based responder when ANTHROPIC_API_KEY is unset.
"""

import time

import httpx

from app.core.config import AGMARKNET_API_KEY

# Public resource id for the Agmarknet daily mandi price dataset on
# data.gov.in — same for every consumer, only the api-key is caller-specific.
_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
_BASE_URL = f"https://api.data.gov.in/resource/{_RESOURCE_ID}"

_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL_SECONDS = 6 * 3600


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_mandi_prices(crop: str, state: str, limit: int = 6) -> dict:
    if not AGMARKNET_API_KEY:
        return {"configured": False, "prices": []}

    cache_key = f"{state}:{crop}"
    cached = _CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    params = {
        "api-key": AGMARKNET_API_KEY,
        "format": "json",
        "limit": limit,
        "filters[state]": state,
        "filters[commodity]": crop,
    }
    try:
        # data.gov.in's gateway silently drops (no error, just hangs to
        # timeout) requests carrying httpx's default "python-httpx/x.y"
        # User-Agent — a browser-like one gets a normal response.
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AgriNova/1.0)"}
        with httpx.Client(timeout=8.0, headers=headers) as client:
            resp = client.get(_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        return {"configured": True, "prices": [], "error": "unavailable"}

    prices = [
        {
            "market": r.get("market"),
            "district": r.get("district"),
            "commodity": r.get("commodity"),
            "variety": r.get("variety"),
            "min_price": _to_float(r.get("min_price")),
            "max_price": _to_float(r.get("max_price")),
            "modal_price": _to_float(r.get("modal_price")),
            "arrival_date": r.get("arrival_date"),
        }
        for r in data.get("records", [])
    ]
    result = {"configured": True, "prices": prices}
    _CACHE[cache_key] = (time.time(), result)
    return result
