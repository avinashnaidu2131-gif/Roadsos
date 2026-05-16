"""
RoadSoS - Emergency Numbers DB Builder
Converts emergency_numbers.json → SQLite for fast offline lookup
Run once to seed the database: python build_emergency_db.py
"""

import json
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "../data/emergency_numbers.json")
DB_PATH   = os.path.join(BASE_DIR, "../data/roadsos.db")


def build_db():
    with open(JSON_PATH, "r") as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # ── Schema ──────────────────────────────────────────────────────────────
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS countries (
            code         TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            calling_code TEXT
        );

        CREATE TABLE IF NOT EXISTS emergency_numbers (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            region       TEXT DEFAULT 'national',
            service      TEXT NOT NULL,   -- police / ambulance / fire / emergency / …
            number       TEXT NOT NULL,
            FOREIGN KEY (country_code) REFERENCES countries(code)
        );

        CREATE INDEX IF NOT EXISTS idx_country_service
            ON emergency_numbers(country_code, service);
    """)

    inserted_countries = 0
    inserted_numbers   = 0

    for code, country in data["countries"].items():
        cur.execute(
            "INSERT OR REPLACE INTO countries VALUES (?, ?, ?)",
            (code, country["name"], country.get("calling_code", ""))
        )
        inserted_countries += 1

        # National numbers
        for service, number in country.get("national", {}).items():
            cur.execute(
                "INSERT INTO emergency_numbers (country_code, region, service, number) VALUES (?,?,?,?)",
                (code, "national", service, number)
            )
            inserted_numbers += 1

        # State / region numbers (India etc.)
        for region, numbers in country.get("states", {}).items():
            for service, number in numbers.items():
                cur.execute(
                    "INSERT INTO emergency_numbers (country_code, region, service, number) VALUES (?,?,?,?)",
                    (code, region, service, number)
                )
                inserted_numbers += 1

    conn.commit()
    conn.close()

    print(f"✅ Database built: {DB_PATH}")
    print(f"   Countries : {inserted_countries}")
    print(f"   Numbers   : {inserted_numbers}")


# ── Quick lookup helpers (used by other modules) ─────────────────────────────

def get_emergency_numbers(country_code: str, region: str = None) -> dict:
    """
    Returns a dict of {service: number} for a country + optional region.
    Falls back to national numbers if region not found.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    results = {}

    # Try region-specific first (e.g. Telangana)
    if region:
        cur.execute(
            "SELECT service, number FROM emergency_numbers WHERE country_code=? AND region=?",
            (country_code.upper(), region)
        )
        for row in cur.fetchall():
            results[row["service"]] = row["number"]

    # Always fill in national numbers for anything not found above
    cur.execute(
        "SELECT service, number FROM emergency_numbers WHERE country_code=? AND region='national'",
        (country_code.upper(),)
    )
    for row in cur.fetchall():
        if row["service"] not in results:          # region overrides national
            results[row["service"]] = row["number"]

    conn.close()
    return results


def get_country_name(country_code: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT name FROM countries WHERE code=?", (country_code.upper(),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "Unknown"


def list_all_countries() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("SELECT code, name, calling_code FROM countries ORDER BY name")
    countries = [dict(r) for r in cur.fetchall()]
    conn.close()
    return countries


# ── CLI test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    build_db()

    print("\n── Test: India / Telangana ──")
    nums = get_emergency_numbers("IN", "Telangana")
    for svc, num in nums.items():
        print(f"  {svc:30s} → {num}")

    print("\n── Test: UK ──")
    nums = get_emergency_numbers("GB")
    for svc, num in nums.items():
        print(f"  {svc:30s} → {num}")

    print(f"\n── Total countries in DB: {len(list_all_countries())} ──")
