"""
RoadSoS — Static Offline Seeder
Run:  python modules/static_seed.py

Loads a hand-curated dataset of real emergency facilities into the
SQLite cache instantly — no internet connection required.

Use this to guarantee the app has *something* to show before a live
cache_seeder.py run has completed.  The static data is intentionally
conservative (only facilities whose existence is highly reliable).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.cache_manager import save_to_cache, init_db

# ─────────────────────────────────────────────────────────────────────────────
# Format per facility:
#   {"name": str, "lat": float, "lon": float,
#    "address": str, "phone": str, "type": str,
#    "distance_m": 0, "distance_text": "0 m", "source": "static"}
# ─────────────────────────────────────────────────────────────────────────────

STATIC_DATA = {

    # ── Hyderabad ─────────────────────────────────────────────────────────────
    "Hyderabad": {
        "lat": 17.3850, "lon": 78.4867, "country": "IN",
        "hospital": [
            {"name": "Nizam's Institute of Medical Sciences",  "lat": 17.4138, "lon": 78.4504, "address": "Punjagutta, Hyderabad", "phone": "040-23489000"},
            {"name": "Yashoda Hospital Secunderabad",          "lat": 17.4401, "lon": 78.4983, "address": "Neredmet, Secunderabad", "phone": "040-45674567"},
            {"name": "Apollo Hospitals Jubilee Hills",         "lat": 17.4156, "lon": 78.4242, "address": "Film Nagar, Jubilee Hills", "phone": "040-23607777"},
            {"name": "Care Hospital Banjara Hills",            "lat": 17.4143, "lon": 78.4371, "address": "Road No. 1, Banjara Hills", "phone": "040-30419999"},
            {"name": "Osmania General Hospital",               "lat": 17.3800, "lon": 78.4750, "address": "Afzalgunj, Hyderabad",     "phone": "040-24600101"},
        ],
        "police": [
            {"name": "Hyderabad City Police HQ",               "lat": 17.3616, "lon": 78.4747, "address": "Basheerbagh, Hyderabad",   "phone": "040-27852425"},
            {"name": "Banjara Hills Police Station",           "lat": 17.4156, "lon": 78.4350, "address": "Road No. 12, Banjara Hills", "phone": "040-23548006"},
            {"name": "Secunderabad Police Station",            "lat": 17.4399, "lon": 78.4983, "address": "Secunderabad",             "phone": "040-27802188"},
        ],
        "ambulance": [
            {"name": "EMRI 108 Telangana HQ",                  "lat": 17.3950, "lon": 78.4850, "address": "Hyderabad",               "phone": "108"},
            {"name": "NIMS Emergency",                         "lat": 17.4138, "lon": 78.4504, "address": "Punjagutta, Hyderabad",   "phone": "040-23489111"},
        ],
        "towing": [
            {"name": "Hyderabad Traffic Police Towing",        "lat": 17.3800, "lon": 78.4750, "address": "Afzalgunj, Hyderabad",   "phone": "040-23261111"},
        ],
    },

    # ── Mumbai ────────────────────────────────────────────────────────────────
    "Mumbai": {
        "lat": 19.0760, "lon": 72.8777, "country": "IN",
        "hospital": [
            {"name": "KEM Hospital",                           "lat": 18.9985, "lon": 72.8375, "address": "Parel, Mumbai",           "phone": "022-24107000"},
            {"name": "Lilavati Hospital",                      "lat": 19.0508, "lon": 72.8282, "address": "Bandra West, Mumbai",     "phone": "022-26751000"},
            {"name": "Breach Candy Hospital",                  "lat": 18.9706, "lon": 72.8067, "address": "Breach Candy, Mumbai",   "phone": "022-23667888"},
            {"name": "Hinduja Hospital",                       "lat": 19.0039, "lon": 72.8342, "address": "Mahim, Mumbai",          "phone": "022-24452222"},
            {"name": "Nair Hospital",                          "lat": 18.9732, "lon": 72.8327, "address": "Mumbai Central",         "phone": "022-23027600"},
        ],
        "police": [
            {"name": "Mumbai Police HQ",                       "lat": 18.9355, "lon": 72.8330, "address": "Crawford Market, Mumbai", "phone": "022-22621855"},
            {"name": "Bandra Police Station",                  "lat": 19.0596, "lon": 72.8295, "address": "Bandra West, Mumbai",    "phone": "022-26550433"},
        ],
        "ambulance": [
            {"name": "EMRI 108 Maharashtra",                   "lat": 19.0760, "lon": 72.8777, "address": "Mumbai",                 "phone": "108"},
            {"name": "BrihanMumbai Municipal Corporation EMS", "lat": 18.9355, "lon": 72.8330, "address": "Crawford Market",        "phone": "022-24915100"},
        ],
        "towing": [
            {"name": "Mumbai Traffic Police Towing",           "lat": 19.0760, "lon": 72.8777, "address": "Mumbai",                 "phone": "022-24150190"},
        ],
    },

    # ── Delhi ─────────────────────────────────────────────────────────────────
    "Delhi": {
        "lat": 28.6139, "lon": 77.2090, "country": "IN",
        "hospital": [
            {"name": "AIIMS New Delhi",                        "lat": 28.5672, "lon": 77.2100, "address": "Ansari Nagar, New Delhi", "phone": "011-26588500"},
            {"name": "Safdarjung Hospital",                    "lat": 28.5680, "lon": 77.2051, "address": "Ring Road, New Delhi",    "phone": "011-26730000"},
            {"name": "Sir Ganga Ram Hospital",                 "lat": 28.6431, "lon": 77.1907, "address": "Rajinder Nagar, Delhi",  "phone": "011-25750000"},
            {"name": "Apollo Hospitals Sarita Vihar",          "lat": 28.5282, "lon": 77.2872, "address": "Sarita Vihar, Delhi",   "phone": "011-29871090"},
            {"name": "GTB Hospital",                           "lat": 28.6765, "lon": 77.3055, "address": "Dilshad Garden, Delhi",  "phone": "011-22581571"},
        ],
        "police": [
            {"name": "Delhi Police HQ",                        "lat": 28.6283, "lon": 77.2219, "address": "ITO, New Delhi",         "phone": "011-23490000"},
            {"name": "Connaught Place Police Station",         "lat": 28.6329, "lon": 77.2195, "address": "Connaught Place",        "phone": "011-23343673"},
        ],
        "ambulance": [
            {"name": "CATS Delhi (Centralised Accident & Trauma)", "lat": 28.6139, "lon": 77.2090, "address": "New Delhi",          "phone": "102"},
            {"name": "AIIMS Emergency",                        "lat": 28.5672, "lon": 77.2100, "address": "AIIMS, Ansari Nagar",    "phone": "011-26588700"},
        ],
        "towing": [
            {"name": "Delhi Traffic Police Control",           "lat": 28.6283, "lon": 77.2219, "address": "ITO, New Delhi",         "phone": "011-25844444"},
        ],
    },

    # ── Bengaluru ─────────────────────────────────────────────────────────────
    "Bengaluru": {
        "lat": 12.9716, "lon": 77.5946, "country": "IN",
        "hospital": [
            {"name": "Victoria Hospital",                      "lat": 12.9634, "lon": 77.5760, "address": "K R Market, Bengaluru",  "phone": "080-26706209"},
            {"name": "Manipal Hospital Old Airport Road",      "lat": 12.9611, "lon": 77.6478, "address": "HAL Airport Road",       "phone": "080-25023333"},
            {"name": "Apollo Hospital Bannerghatta",           "lat": 12.8918, "lon": 77.5970, "address": "Bannerghatta Road",      "phone": "080-26304050"},
            {"name": "Fortis Hospital Rajajinagar",            "lat": 12.9954, "lon": 77.5534, "address": "Rajajinagar, Bengaluru", "phone": "080-66214444"},
            {"name": "St. John's Medical College Hospital",    "lat": 12.9456, "lon": 77.6167, "address": "Koramangala, Bengaluru", "phone": "080-22065000"},
        ],
        "police": [
            {"name": "Bengaluru City Police HQ",               "lat": 12.9805, "lon": 77.5963, "address": "Infantry Road",          "phone": "080-22868444"},
            {"name": "Koramangala Police Station",             "lat": 12.9352, "lon": 77.6245, "address": "Koramangala",            "phone": "080-25502228"},
        ],
        "ambulance": [
            {"name": "EMRI 108 Karnataka",                     "lat": 12.9716, "lon": 77.5946, "address": "Bengaluru",              "phone": "108"},
            {"name": "Arogya Kavacha 108",                     "lat": 12.9716, "lon": 77.5946, "address": "Bengaluru",              "phone": "108"},
        ],
        "towing": [
            {"name": "Bengaluru Traffic Police Towing",        "lat": 12.9805, "lon": 77.5963, "address": "Infantry Road",          "phone": "080-22868444"},
        ],
    },

    # ── Chennai ───────────────────────────────────────────────────────────────
    "Chennai": {
        "lat": 13.0827, "lon": 80.2707, "country": "IN",
        "hospital": [
            {"name": "Rajiv Gandhi Government General Hospital", "lat": 13.0816, "lon": 80.2667, "address": "Park Town, Chennai",   "phone": "044-25305000"},
            {"name": "Apollo Hospital Greams Road",             "lat": 13.0628, "lon": 80.2543, "address": "Greams Road, Chennai",  "phone": "044-28296666"},
            {"name": "MIOT International",                      "lat": 13.0216, "lon": 80.1785, "address": "Manappakkam, Chennai",  "phone": "044-42002288"},
            {"name": "Fortis Malar Hospital",                   "lat": 13.0045, "lon": 80.2564, "address": "Adyar, Chennai",       "phone": "044-42892222"},
        ],
        "police": [
            {"name": "Chennai Police HQ",                       "lat": 13.0801, "lon": 80.2685, "address": "Commissioner's Office, Vepery", "phone": "044-28447750"},
        ],
        "ambulance": [
            {"name": "EMRI 108 Tamil Nadu",                     "lat": 13.0827, "lon": 80.2707, "address": "Chennai",               "phone": "108"},
        ],
        "towing": [
            {"name": "Chennai Traffic Police",                  "lat": 13.0801, "lon": 80.2685, "address": "Vepery, Chennai",       "phone": "044-28594750"},
        ],
    },

    # ── Singapore ─────────────────────────────────────────────────────────────
    "Singapore": {
        "lat": 1.3521, "lon": 103.8198, "country": "SG",
        "hospital": [
            {"name": "Singapore General Hospital",              "lat": 1.2797, "lon": 103.8352, "address": "Outram Road, Singapore",  "phone": "+65-62223322"},
            {"name": "Tan Tock Seng Hospital",                  "lat": 1.3215, "lon": 103.8459, "address": "Novena, Singapore",       "phone": "+65-63577777"},
            {"name": "National University Hospital",            "lat": 1.2944, "lon": 103.7832, "address": "Kent Ridge, Singapore",   "phone": "+65-67795555"},
        ],
        "police": [
            {"name": "Singapore Police Force HQ",               "lat": 1.3081, "lon": 103.8666, "address": "New Phoenix Park",        "phone": "999"},
            {"name": "Central Police Division",                 "lat": 1.2866, "lon": 103.8520, "address": "Cantonment Road",         "phone": "+65-62991699"},
        ],
        "ambulance": [
            {"name": "Singapore Civil Defence Force (SCDF)",    "lat": 1.3521, "lon": 103.8198, "address": "Singapore",               "phone": "995"},
        ],
        "towing": [
            {"name": "LTA Vehicle Recovery",                    "lat": 1.3521, "lon": 103.8198, "address": "Singapore",               "phone": "1800-2255582"},
        ],
    },

    # ── Dubai ─────────────────────────────────────────────────────────────────
    "Dubai": {
        "lat": 25.2048, "lon": 55.2708, "country": "AE",
        "hospital": [
            {"name": "Rashid Hospital",                         "lat": 25.2286, "lon": 55.3271, "address": "Oud Metha, Dubai",        "phone": "+971-4-2192000"},
            {"name": "Dubai Hospital",                          "lat": 25.2584, "lon": 55.3005, "address": "Al Baraha, Dubai",        "phone": "+971-4-2190000"},
            {"name": "American Hospital Dubai",                 "lat": 25.2295, "lon": 55.3095, "address": "Oud Metha, Dubai",        "phone": "+971-4-3364444"},
        ],
        "police": [
            {"name": "Dubai Police HQ",                         "lat": 25.1972, "lon": 55.2744, "address": "Al Twar, Dubai",          "phone": "999"},
            {"name": "Deira Police Station",                    "lat": 25.2697, "lon": 55.3094, "address": "Deira, Dubai",            "phone": "+971-4-2269999"},
        ],
        "ambulance": [
            {"name": "Dubai Corporation for Ambulance Services", "lat": 25.2048, "lon": 55.2708, "address": "Dubai",                 "phone": "998"},
        ],
        "towing": [
            {"name": "Dubai Police Traffic Towing",             "lat": 25.2048, "lon": 55.2708, "address": "Dubai",                  "phone": "901"},
        ],
    },

    # ── London ────────────────────────────────────────────────────────────────
    "London": {
        "lat": 51.5074, "lon": -0.1278, "country": "GB",
        "hospital": [
            {"name": "St Thomas' Hospital",                     "lat": 51.4985, "lon": -0.1187, "address": "Westminster Bridge Rd, London", "phone": "+44-20-71887188"},
            {"name": "King's College Hospital",                 "lat": 51.4680, "lon": -0.0932, "address": "Denmark Hill, London",    "phone": "+44-20-33299000"},
            {"name": "Royal London Hospital",                   "lat": 51.5188, "lon": -0.0597, "address": "Whitechapel, London",     "phone": "+44-20-37777000"},
        ],
        "police": [
            {"name": "Metropolitan Police HQ",                  "lat": 51.5005, "lon": -0.1253, "address": "New Scotland Yard, London", "phone": "999"},
            {"name": "City of London Police",                   "lat": 51.5154, "lon": -0.0921, "address": "Wood Street, London",    "phone": "999"},
        ],
        "ambulance": [
            {"name": "London Ambulance Service",                "lat": 51.5074, "lon": -0.1278, "address": "London",                  "phone": "999"},
        ],
        "towing": [
            {"name": "TRACE London (TfL Vehicle Recovery)",     "lat": 51.5074, "lon": -0.1278, "address": "London",                  "phone": "0845-2060410"},
        ],
    },

    # ── New York ──────────────────────────────────────────────────────────────
    "New York": {
        "lat": 40.7128, "lon": -74.0060, "country": "US",
        "hospital": [
            {"name": "Bellevue Hospital Center",                "lat": 40.7393, "lon": -73.9749, "address": "First Ave, New York",    "phone": "+1-212-5622000"},
            {"name": "NewYork-Presbyterian Hospital",           "lat": 40.7641, "lon": -73.9546, "address": "York Ave, New York",     "phone": "+1-212-7468000"},
            {"name": "Mount Sinai Hospital",                    "lat": 40.7900, "lon": -73.9526, "address": "Fifth Ave, New York",    "phone": "+1-212-2417981"},
        ],
        "police": [
            {"name": "NYPD One Police Plaza",                   "lat": 40.7127, "lon": -74.0023, "address": "One Police Plaza, NYC",  "phone": "911"},
            {"name": "Midtown North Precinct",                  "lat": 40.7640, "lon": -73.9878, "address": "W 54th St, Manhattan",   "phone": "+1-212-7671411"},
        ],
        "ambulance": [
            {"name": "NYC Emergency Medical Services",          "lat": 40.7128, "lon": -74.0060, "address": "New York",               "phone": "911"},
        ],
        "towing": [
            {"name": "NYPD Traffic Pound — Manhattan",          "lat": 40.7517, "lon": -74.0027, "address": "West Side Highway, NYC", "phone": "+1-212-5949463"},
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
def _normalise(items, stype):
    """Add required fields that cache_manager.get_cached expects."""
    out = []
    for it in items:
        out.append({
            "name":          it["name"],
            "lat":           it["lat"],
            "lon":           it["lon"],
            "address":       it.get("address", ""),
            "phone":         it.get("phone", ""),
            "type":          stype,
            "distance_m":    0,
            "distance_text": "0 m",
            "source":        "static",
        })
    return out


def seed_static():
    init_db()
    total_inserted = 0
    print(f"\n{'═'*55}")
    print(f"  RoadSoS Static Offline Seeder")
    print(f"  {len(STATIC_DATA)} cities — no internet required")
    print(f"{'═'*55}\n")

    for city, data in STATIC_DATA.items():
        lat     = data["lat"]
        lon     = data["lon"]
        country = data.get("country", "IN")
        city_total = 0
        print(f"📍 {city}")
        for stype in ["hospital", "police", "ambulance", "towing"]:
            items = _normalise(data.get(stype, []), stype)
            if items:
                save_to_cache(lat, lon, stype, items, city=city, country=country)
                city_total += len(items)
                print(f"   ✅ {stype:<12} — {len(items)} facilities")
            else:
                print(f"   —  {stype:<12} — (no static data)")
        total_inserted += city_total
        print()

    print(f"{'═'*55}")
    print(f"  ✅ Static seed complete — {total_inserted} facilities loaded.")
    print(f"  Offline cache is ready for immediate use.")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    seed_static()
