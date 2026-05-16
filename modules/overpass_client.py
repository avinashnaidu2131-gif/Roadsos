"""
RoadSoS — Overpass API Client
Queries OpenStreetMap for nearby emergency services.
Free, no API key needed.
"""

import requests
from config import Config

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

SERVICE_TAGS = {
    "hospital": [
        '["amenity"="hospital"]',
        '["amenity"="clinic"]',
    ],
    "police": [
        '["amenity"="police"]',
    ],
    "ambulance": [
        '["emergency"="ambulance_station"]',
        '["amenity"="hospital"]["emergency"="yes"]',
    ],
    "towing": [
        '["shop"="car_repair"]',
        '["service"="tyres"]',
    ],
    "fire": [
        '["amenity"="fire_station"]',
    ],
}


def build_query(lat, lon, service_type, radius):
    tags = SERVICE_TAGS.get(service_type, SERVICE_TAGS["hospital"])
    parts = []
    for tag in tags:
        parts.append(f'node{tag}(around:{radius},{lat},{lon});')
        parts.append(f'way{tag}(around:{radius},{lat},{lon});')
    return f'[out:json][timeout:15];({"".join(parts)});out center tags;'


def query_overpass(lat, lon, service_type, radius=None):
    """Returns sorted list of nearby services. Empty list on any error."""
    if radius is None:
        radius = Config.DEFAULT_RADIUS

    query = build_query(lat, lon, service_type, radius)
    headers = {
        "User-Agent": "RoadSoS/1.0 (Road Safety Hackathon 2026)",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    for mirror in OVERPASS_MIRRORS:
        try:
            resp = requests.post(
                mirror,
                data={"data": query},
                headers=headers,
                timeout=Config.OVERPASS_TIMEOUT
            )
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
            break  # success — stop trying mirrors
        except Exception as e:
            print(f"[Overpass] {mirror} failed: {e}")
            elements = []
            continue

    results = []
    for el in elements:
        tags = el.get("tags", {})
        if el["type"] == "node":
            rlat, rlon = el.get("lat"), el.get("lon")
        else:
            c = el.get("center", {})
            rlat, rlon = c.get("lat"), c.get("lon")
        if not rlat or not rlon:
            continue

        name = (tags.get("name") or tags.get("name:en") or
                service_type.replace("_", " ").title())
        addr_parts = [tags.get("addr:housenumber",""), tags.get("addr:street",""),
                      tags.get("addr:suburb",""), tags.get("addr:city","")]
        address = ", ".join(p for p in addr_parts if p) or "Address unavailable"
        phone = tags.get("phone") or tags.get("contact:phone") or ""
        dist = _haversine(lat, lon, rlat, rlon)

        results.append({
            "name": name, "lat": rlat, "lon": rlon,
            "address": address, "phone": phone, "type": service_type,
            "distance_m": round(dist), "distance_text": _fmt_dist(dist),
            "source": "live"
        })

    results.sort(key=lambda x: x["distance_m"])
    return results[:Config.MAX_RESULTS]


def _haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371000
    p1, p2 = radians(lat1), radians(lat2)
    dp, dl = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


def _fmt_dist(m):
    return f"{int(m)} m" if m < 1000 else f"{m/1000:.1f} km"
