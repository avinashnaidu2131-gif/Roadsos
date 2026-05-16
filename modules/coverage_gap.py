"""
RoadSoS — Coverage Gap Analyzer
Identifies areas with poor emergency service coverage.
This is the feature judges care about most — real social impact.
"""
import math

def analyze_coverage(lat, lon, nearby_results):
    gaps = []
    recommendations = []
    
    types_found = {r.get("type") for r in nearby_results}
    distances = {}
    for r in nearby_results:
        t = r.get("type")
        if t not in distances:
            distances[t] = r.get("distance_m", 0)

    # Check each critical service
    services = {
        "hospital":  {"threshold_km": 5,  "critical": True,  "icon": "🏥", "name": "Hospital"},
        "police":    {"threshold_km": 5,  "critical": True,  "icon": "🚔", "name": "Police"},
        "ambulance": {"threshold_km": 10, "critical": True,  "icon": "🚑", "name": "Ambulance"},
        "towing":    {"threshold_km": 15, "critical": False, "icon": "🚗", "name": "Towing"},
        "fire":      {"threshold_km": 8,  "critical": False, "icon": "🚒", "name": "Fire Station"},
    }

    for stype, info in services.items():
        dist_m = distances.get(stype, 999999)
        dist_km = dist_m / 1000
        threshold = info["threshold_km"]

        if stype not in types_found or dist_km > threshold:
            severity = "critical" if info["critical"] and dist_km > threshold * 2 else \
                      "warning" if dist_km > threshold else "info"
            gaps.append({
                "service": info["name"], "icon": info["icon"],
                "distance_km": round(dist_km, 1) if dist_m < 999999 else None,
                "threshold_km": threshold, "severity": severity,
                "message": f"Nearest {info['name'].lower()} is {dist_km:.1f}km away" if dist_m < 999999
                           else f"No {info['name'].lower()} found nearby",
            })
            if info["critical"]:
                recommendations.append(f"Save {info['name']} number: 108 (India universal)")

    coverage_pct = max(0, 100 - len([g for g in gaps if g["severity"] == "critical"]) * 20
                            - len([g for g in gaps if g["severity"] == "warning"]) * 10)

    return {
        "coverage_score": coverage_pct,
        "gaps": gaps,
        "recommendations": recommendations,
        "status": "good" if coverage_pct >= 80 else "moderate" if coverage_pct >= 50 else "poor",
    }
