"""
RoadSoS — Cache Manager
Reads and writes nearby-services data to SQLite for offline use.
"""

import sqlite3
import json
import os
from math import radians, sin, cos, sqrt, atan2
from config import Config


def _get_conn():
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT NOT NULL,
            name        TEXT NOT NULL,
            lat         REAL NOT NULL,
            lon         REAL NOT NULL,
            address     TEXT,
            phone       TEXT,
            city        TEXT,
            country     TEXT DEFAULT 'IN',
            extra       TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON services(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_city ON services(city)")
    conn.commit()
    conn.close()


def save_to_cache(lat, lon, service_type, items, city=None, country="IN"):
    """Upsert live results into SQLite cache."""
    conn = _get_conn()
    for item in items:
        existing = conn.execute(
            "SELECT id FROM services WHERE name=? AND type=? AND lat=? AND lon=?",
            (item["name"], service_type, item["lat"], item["lon"])
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO services (type, name, lat, lon, address, phone, city, country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                service_type, item["name"], item["lat"], item["lon"],
                item.get("address", ""), item.get("phone", ""),
                city or "", country
            ))
    conn.commit()
    conn.close()


def get_cached(lat, lon, service_type, radius_m=15000):
    """
    Return cached services of given type within radius_m metres of lat/lon.
    Uses bounding-box pre-filter then precise haversine check.
    """
    # Rough degree delta (1 deg lat ≈ 111 km)
    delta = radius_m / 111000
    lat_min, lat_max = lat - delta, lat + delta
    lon_min, lon_max = lon - delta, lon + delta

    conn = _get_conn()
    rows = conn.execute("""
        SELECT * FROM services
        WHERE type=?
          AND lat BETWEEN ? AND ?
          AND lon BETWEEN ? AND ?
    """, (service_type, lat_min, lat_max, lon_min, lon_max)).fetchall()
    conn.close()

    results = []
    for row in rows:
        dist = _haversine(lat, lon, row["lat"], row["lon"])
        if dist <= radius_m:
            results.append({
                "name":          row["name"],
                "lat":           row["lat"],
                "lon":           row["lon"],
                "address":       row["address"] or "Address unavailable",
                "phone":         row["phone"] or "",
                "type":          row["type"],
                "distance_m":    round(dist),
                "distance_text": _fmt(dist),
                "source":        "cache",
            })

    results.sort(key=lambda x: x["distance_m"])
    return results[:Config.MAX_RESULTS]


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = radians(lat1), radians(lat2)
    dp, dl = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


def _fmt(m):
    return f"{int(m)} m" if m < 1000 else f"{m/1000:.1f} km"


# Initialise DB on import
init_db()
