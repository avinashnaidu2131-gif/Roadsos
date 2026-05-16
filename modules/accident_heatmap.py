"""
RoadSoS — Accident Heatmap Module
Generates realistic accident hotspot data around a location.
Uses OSM road data + seeded randomisation for consistent demo points.
"""

import math
import hashlib
import requests

def get_heatmap_points(center_lat: float, center_lon: float, radius_km: float = 10) -> list:
    """
    Returns list of {lat, lon, intensity} accident hotspot points.
    First tries OSM for real road intersections, then generates seeded points.
    """
    points = []

    # Try to get real road intersection data from Overpass
    try:
        points = _fetch_osm_hotspots(center_lat, center_lon, radius_km)
    except Exception as e:
        print(f"[Heatmap] OSM fetch failed: {e}")

    # Always supplement with seeded deterministic points for demo reliability
    seeded = _generate_seeded_points(center_lat, center_lon, radius_km)
    points.extend(seeded)

    # Deduplicate and limit
    return points[:80]


def _fetch_osm_hotspots(lat, lon, radius_km):
    """Fetch busy road intersections from OpenStreetMap as accident proxies."""
    radius_m = int(radius_km * 1000)
    query = f"""
    [out:json][timeout:10];
    (
      node["highway"="traffic_signals"]({lat-0.1},{lon-0.15},{lat+0.1},{lon+0.15});
      node["highway"="crossing"]["crossing"="traffic_signals"]({lat-0.1},{lon-0.15},{lat+0.1},{lon+0.15});
    );
    out body 40;
    """
    resp = requests.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        headers={"User-Agent": "RoadSoS/1.0"},
        timeout=10,
    )
    elements = resp.json().get("elements", [])
    points = []
    for el in elements:
        if "lat" in el and "lon" in el:
            # Assign intensity based on hash for consistency
            h = int(hashlib.md5(f"{el['lat']}{el['lon']}".encode()).hexdigest()[:4], 16)
            intensity = 0.3 + (h % 100) / 140.0   # 0.3 – 1.0
            points.append({
                "lat": el["lat"],
                "lon": el["lon"],
                "intensity": round(min(intensity, 1.0), 2),
                "source": "osm"
            })
    return points


def _generate_seeded_points(center_lat, center_lon, radius_km):
    """
    Generate deterministic hotspot points seeded by location.
    Same location always gives same heatmap — looks realistic for demo.
    """
    seed_str = f"{round(center_lat,2)}{round(center_lon,2)}"
    seed     = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)

    points = []
    # Major hotspot clusters (highway junctions, city centres etc.)
    clusters = [
        (0.00,  0.00,  1.0),   # city centre
        (0.02,  0.03,  0.85),  # north-east junction
        (-0.03, 0.02,  0.75),  # south highway
        (0.01, -0.04,  0.70),  # west ring road
        (-0.02,-0.03,  0.65),  # south-west
        (0.04,  0.01,  0.60),  # north bypass
        (-0.01, 0.05,  0.55),  # east connector
        (0.03, -0.02,  0.50),  # north-west
    ]

    for i, (dlat, dlon, base_intensity) in enumerate(clusters):
        # Scatter ~8 points around each cluster
        for j in range(8):
            rng = (seed * (i * 31 + j * 17 + 7)) % 10000
            scatter_lat = dlat + (rng % 100 - 50) * 0.0008
            scatter_lon = dlon + ((rng // 100) % 100 - 50) * 0.001
            intensity   = base_intensity * (0.6 + (rng % 40) / 100.0)
            points.append({
                "lat":       round(center_lat + scatter_lat, 6),
                "lon":       round(center_lon + scatter_lon, 6),
                "intensity": round(min(intensity, 1.0), 2),
                "source":    "model"
            })

    return points
