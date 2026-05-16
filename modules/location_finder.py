"""
RoadSoS — Location Finder
Combines live Overpass API with offline SQLite cache.
Falls back to cache automatically when network is unavailable.
"""

import requests
from config import Config
from modules.overpass_client import query_overpass
from modules.cache_manager import get_cached, save_to_cache

SUPPORTED_TYPES = ["hospital", "police", "ambulance", "towing", "fire"]


def find_nearby(lat, lon, service_type="all", radius=None):
    """
    Main entry point. Returns dict with results for one or all service types.
    Automatically falls back to offline cache if live query fails.
    """
    if radius is None:
        radius = Config.DEFAULT_RADIUS

    if service_type == "all":
        results = {}
        for stype in SUPPORTED_TYPES:
            results[stype] = _find_single(lat, lon, stype, radius)
        return {"type": "all", "results": results, "lat": lat, "lon": lon}

    if service_type not in SUPPORTED_TYPES:
        return {"error": f"Unknown service type '{service_type}'. "
                         f"Choose from: {', '.join(SUPPORTED_TYPES)}"}

    items = _find_single(lat, lon, service_type, radius)
    return {
        "type": service_type,
        "results": items,
        "count": len(items),
        "lat": lat,
        "lon": lon,
        "radius_m": radius,
    }


def _find_single(lat, lon, service_type, radius):
    """Try live API first, fall back to cache, expand radius if empty."""
    # Skip live if offline mode forced
    if not Config.OFFLINE_MODE:
        items = query_overpass(lat, lon, service_type, radius)
        if items:
            save_to_cache(lat, lon, service_type, items)
            return items

        # Retry with double radius before giving up on live
        items = query_overpass(lat, lon, service_type, radius * 2)
        if items:
            save_to_cache(lat, lon, service_type, items)
            return items

    # Offline fallback
    cached = get_cached(lat, lon, service_type, radius * 3)
    if cached:
        for item in cached:
            item["source"] = "cache"
        return cached

    return []


def geocode_address(address):
    """
    Convert address string to (lat, lon) using Nominatim (free, no key).
    Returns (lat, lon) tuple or None on failure.
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "RoadSoS/1.0"},
            timeout=8
        )
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"[Geocode] {e}")
    return None
