"""
RoadSoS — Hospital Bed Availability Module
Simulates real-time bed availability for demo.
Uses hospital name + time as seed for realistic fluctuation.
"""
import hashlib, time, math

def get_bed_availability(hospital_name: str, lat: float = 0) -> dict:
    seed_str = hospital_name.lower().strip() + str(int(time.time() // 3600))
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:6], 16)

    def rng(offset, max_val):
        return (seed + offset * 7919) % max_val

    total_general  = 20 + rng(1, 80)
    total_icu      = 5  + rng(2, 15)
    total_emergency= 3  + rng(3, 10)

    occ_rate = 0.4 + (rng(4, 50) / 100)
    avail_general   = max(0, total_general   - int(total_general   * occ_rate))
    avail_icu       = max(0, total_icu       - int(total_icu       * (occ_rate + 0.1)))
    avail_emergency = max(0, total_emergency - int(total_emergency * (occ_rate - 0.1)))

    def status(avail, total):
        pct = avail / total if total else 0
        if pct > 0.3: return "available"
        if pct > 0.1: return "limited"
        return "full"

    return {
        "hospital": hospital_name,
        "last_updated": "Live (simulated)",
        "beds": {
            "general":   {"available": avail_general,   "total": total_general,   "status": status(avail_general,   total_general)},
            "icu":       {"available": avail_icu,        "total": total_icu,        "status": status(avail_icu,        total_icu)},
            "emergency": {"available": avail_emergency,  "total": total_emergency,  "status": status(avail_emergency,  total_emergency)},
        },
        "accepts_emergency": avail_emergency > 0,
        "wait_time_min": max(0, int(20 - avail_emergency * 5)),
        "note": "Bed data is simulated for demonstration purposes."
    }
