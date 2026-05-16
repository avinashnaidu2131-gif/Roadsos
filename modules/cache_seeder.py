"""
RoadSoS — Cache Seeder  (v2 — 50 cities)
Run once:  python modules/cache_seeder.py [--dry-run] [--cities N] [--resume]

Features
--------
• 50 cities across India + major international metros
• Smart retry with exponential back-off (3 attempts per query)
• Progress file — resume interrupted runs with --resume
• --dry-run flag to validate city list without hitting the API
• Polite 1.2 s delay between requests (Overpass fair-use policy)
• Correct save_to_cache signature  (items as 4th arg, city as 5th)
"""

import sys, os, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.overpass_client import query_overpass
from modules.cache_manager import save_to_cache

# ── Progress file (stores completed "city|type" keys) ────────────────────────
PROGRESS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "seed_progress.json"
)

# ── 50-city roster ────────────────────────────────────────────────────────────
CITIES = [
    # ── India — Tier-1 metros ────────────────────────────────────────────────
    ("Hyderabad",          17.3850,  78.4867, 8000, "IN"),
    ("Mumbai",             19.0760,  72.8777, 8000, "IN"),
    ("Delhi",              28.6139,  77.2090, 8000, "IN"),
    ("Bengaluru",          12.9716,  77.5946, 8000, "IN"),
    ("Chennai",            13.0827,  80.2707, 8000, "IN"),
    ("Kolkata",            22.5726,  88.3639, 8000, "IN"),
    ("Pune",               18.5204,  73.8567, 7000, "IN"),
    ("Ahmedabad",          23.0225,  72.5714, 7000, "IN"),
    # ── India — Tier-2 cities ────────────────────────────────────────────────
    ("Jaipur",             26.9124,  75.7873, 6000, "IN"),
    ("Lucknow",            26.8467,  80.9462, 6000, "IN"),
    ("Bhopal",             23.2599,  77.4126, 6000, "IN"),
    ("Indore",             22.7196,  75.8577, 6000, "IN"),
    ("Nagpur",             21.1458,  79.0882, 6000, "IN"),
    ("Patna",              25.5941,  85.1376, 6000, "IN"),
    ("Bhubaneswar",        20.2961,  85.8245, 6000, "IN"),
    ("Visakhapatnam",      17.6868,  83.2185, 6000, "IN"),
    ("Coimbatore",         11.0168,  76.9558, 6000, "IN"),
    ("Kochi",               9.9312,  76.2673, 6000, "IN"),
    ("Thiruvananthapuram",  8.5241,  76.9366, 6000, "IN"),
    ("Guwahati",           26.1445,  91.7362, 6000, "IN"),
    # ── India — Tier-3 / highway nodes ──────────────────────────────────────
    ("Surat",              21.1702,  72.8311, 5000, "IN"),
    ("Vadodara",           22.3072,  73.1812, 5000, "IN"),
    ("Rajkot",             22.3039,  70.8022, 5000, "IN"),
    ("Amritsar",           31.6340,  74.8723, 5000, "IN"),
    ("Chandigarh",         30.7333,  76.7794, 5000, "IN"),
    ("Ludhiana",           30.9010,  75.8573, 5000, "IN"),
    ("Agra",               27.1767,  78.0081, 5000, "IN"),
    ("Varanasi",           25.3176,  82.9739, 5000, "IN"),
    ("Ranchi",             23.3441,  85.3096, 5000, "IN"),
    ("Raipur",             21.2514,  81.6296, 5000, "IN"),
    ("Mysuru",             12.2958,  76.6394, 5000, "IN"),
    ("Mangaluru",          12.8698,  74.8431, 5000, "IN"),
    ("Hubli",              15.3647,  75.1240, 5000, "IN"),
    ("Madurai",             9.9252,  78.1198, 5000, "IN"),
    ("Tiruchirappalli",    10.7905,  78.7047, 5000, "IN"),
    ("Dehradun",           30.3165,  78.0322, 5000, "IN"),
    ("Shimla",             31.1048,  77.1734, 5000, "IN"),
    ("Jammu",              32.7266,  74.8570, 5000, "IN"),
    ("Srinagar",           34.0837,  74.7973, 5000, "IN"),
    ("Jodhpur",            26.2389,  73.0243, 5000, "IN"),
    ("Udaipur",            24.5854,  73.7125, 5000, "IN"),
    ("Aurangabad",         19.8762,  75.3433, 5000, "IN"),
    # ── International metros ─────────────────────────────────────────────────
    ("Singapore",           1.3521, 103.8198, 8000, "SG"),
    ("Kuala Lumpur",        3.1390, 101.6869, 8000, "MY"),
    ("Bangkok",            13.7563, 100.5018, 8000, "TH"),
    ("Dubai",              25.2048,  55.2708, 8000, "AE"),
    ("London",             51.5074,  -0.1278, 8000, "GB"),
    ("New York",           40.7128, -74.0060, 8000, "US"),
    ("Sydney",            -33.8688, 151.2093, 8000, "AU"),
    ("Toronto",            43.6532, -79.3832, 8000, "CA"),
]

SERVICE_TYPES = ["hospital", "police", "ambulance", "towing"]

# ── Retry wrapper ─────────────────────────────────────────────────────────────
def query_with_retry(lat, lon, stype, radius, max_tries=3):
    """Call query_overpass with exponential back-off. Returns list (may be empty)."""
    for attempt in range(1, max_tries + 1):
        try:
            results = query_overpass(lat, lon, stype, radius)
            return results
        except Exception as e:
            wait = 2 ** attempt          # 2s, 4s, 8s
            if attempt < max_tries:
                print(f"      ⚠  attempt {attempt} failed ({e}) — retry in {wait}s")
                time.sleep(wait)
            else:
                raise

# ── Progress helpers ──────────────────────────────────────────────────────────
def load_progress():
    """Return set of completed 'city|type' keys from progress file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE) as f:
                return set(json.load(f).get("done", []))
        except Exception:
            pass
    return set()

def save_progress(done_set):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"done": sorted(done_set)}, f, indent=2)

# ── Main seeder ───────────────────────────────────────────────────────────────
def seed(dry_run=False, limit=None, resume=False):
    cities = CITIES[:limit] if limit else CITIES
    total  = len(cities) * len(SERVICE_TYPES)
    done_keys = load_progress() if resume else set()

    skipped  = sum(1 for c in cities
                   for s in SERVICE_TYPES
                   if f"{c[0]}|{s}" in done_keys)

    print(f"\n{'═'*58}")
    print(f"  RoadSoS Offline Cache Seeder  v2")
    print(f"  {len(cities)} cities × {len(SERVICE_TYPES)} types = {total} queries")
    if resume and skipped:
        print(f"  Resuming — {skipped} already done, skipping them.")
    if dry_run:
        print(f"  DRY-RUN — no API calls will be made.")
    print(f"{'═'*58}\n")

    if dry_run:
        for i, (city, lat, lon, radius, country) in enumerate(cities, 1):
            print(f"  {i:>3}. {city:<26} {lat:>9.4f}, {lon:>10.4f}  r={radius}m  [{country}]")
        print(f"\n  ✅ Dry-run complete — {len(cities)} cities validated.")
        return

    done = skipped
    errors = 0
    t0 = time.time()

    for city, lat, lon, radius, country in cities:
        city_already_done = all(f"{city}|{s}" in done_keys for s in SERVICE_TYPES)
        if city_already_done:
            print(f"  ⏭  {city} — all types already cached, skipping.")
            continue

        print(f"\n📍 {city} ({lat}, {lon})  radius={radius}m  [{country}]")

        for stype in SERVICE_TYPES:
            key = f"{city}|{stype}"
            if key in done_keys:
                print(f"   ⏭  {stype:<12} — already cached")
                continue

            try:
                results = query_with_retry(lat, lon, stype, radius)
                # ── FIXED: results as 4th arg; city/country as named kwargs ──
                if results:
                    save_to_cache(lat, lon, stype, results,
                                  city=city, country=country)
                    print(f"   ✅ {stype:<12} — {len(results):>3} results cached")
                else:
                    print(f"   ⚠  {stype:<12} —   0 results (sparse OSM data)")
                done += 1
                done_keys.add(key)
                save_progress(done_keys)
                time.sleep(1.2)          # Overpass fair-use: ≤1 req/s

            except Exception as e:
                errors += 1
                print(f"   ❌ {stype:<12} — {e}")
                time.sleep(3)

    elapsed = time.time() - t0
    mm, ss  = divmod(int(elapsed), 60)

    print(f"\n{'═'*58}")
    print(f"  Seeding complete in {mm}m {ss}s")
    print(f"  Queries seeded : {done - skipped}/{total - skipped}")
    print(f"  Errors         : {errors}")
    print(f"  Offline cache is ready.  (data/roadsos.db)")
    if errors:
        print(f"\n  ⚠  Re-run with --resume to retry failed queries.")
    print(f"{'═'*58}\n")

    # Clean up progress file once fully done with no errors
    if done >= total and not errors:
        try:
            os.remove(PROGRESS_FILE)
        except OSError:
            pass


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pre-seed RoadSoS offline cache for 50 cities."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate city list without making any API calls."
    )
    parser.add_argument(
        "--cities", type=int, default=None, metavar="N",
        help="Seed only the first N cities (useful for testing)."
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip cities/types already recorded in data/seed_progress.json."
    )
    args = parser.parse_args()

    seed(dry_run=args.dry_run, limit=args.cities, resume=args.resume)
