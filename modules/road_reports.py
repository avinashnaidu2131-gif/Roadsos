"""
RoadSoS — Road Condition Reports Module
Crowdsourced pothole/accident/flood reports.
"""
import sqlite3, os, time, math
from config import Config

DB = Config.DB_PATH

REPORT_TYPES = {
    "pothole":   {"icon": "🕳",  "label": "Pothole"},
    "accident":  {"icon": "💥",  "label": "Accident"},
    "flooding":  {"icon": "🌊",  "label": "Flooding"},
    "roadblock": {"icon": "🚧",  "label": "Road Block"},
    "breakdown": {"icon": "🚗",  "label": "Vehicle Breakdown"},
    "animal":    {"icon": "🐄",  "label": "Animal on Road"},
}

def _conn():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS road_reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lat REAL, lon REAL, type TEXT, description TEXT,
        upvotes INTEGER DEFAULT 0, created_at INTEGER)""")
    c.commit()
    return c

def add_report(lat, lon, rtype, description=""):
    if rtype not in REPORT_TYPES:
        return {"error": f"Invalid type. Use: {', '.join(REPORT_TYPES)}"}
    c = _conn()
    cur = c.execute("INSERT INTO road_reports(lat,lon,type,description,created_at) VALUES(?,?,?,?,?)",
                    (lat, lon, rtype, description, int(time.time())))
    rid = cur.lastrowid; c.commit(); c.close()
    return {"id": rid, "status": "reported", "type": rtype,
            "icon": REPORT_TYPES[rtype]["icon"]}

def get_reports(lat, lon, radius_km=10):
    c = _conn()
    rows = c.execute(
        "SELECT id,lat,lon,type,description,upvotes,created_at FROM road_reports ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    c.close()
    results = []
    for r in rows:
        dlat = r[1] - lat; dlon = r[2] - lon
        dist = math.sqrt(dlat**2 + dlon**2) * 111
        if dist <= radius_km:
            results.append({
                "id": r[0], "lat": r[1], "lon": r[2], "type": r[3],
                "description": r[4], "upvotes": r[5],
                "icon": REPORT_TYPES.get(r[3], {}).get("icon", "⚠"),
                "label": REPORT_TYPES.get(r[3], {}).get("label", r[3]),
                "age_min": max(0, int((time.time() - r[6]) / 60)),
                "dist_km": round(dist, 2),
            })
    return sorted(results, key=lambda x: x["dist_km"])

def upvote_report(report_id):
    c = _conn()
    c.execute("UPDATE road_reports SET upvotes=upvotes+1 WHERE id=?", (report_id,))
    c.commit(); c.close()
    return {"status": "ok"}
