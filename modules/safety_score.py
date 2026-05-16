"""
RoadSoS — Road Safety Score Module
Calculates a real-time safety score for any location based on:
- Distance to nearest emergency services
- Number of accident hotspots nearby
- Road quality reports
- Time of day risk factor
"""
import math, time

def get_safety_score(lat, lon, nearby_results=None, reports=None):
    score = 100
    factors = []

    # Factor 1: Distance to nearest hospital
    if nearby_results:
        hospital_results = [r for r in nearby_results if r.get("type") == "hospital"]
        if hospital_results:
            dist_km = hospital_results[0].get("distance_m", 99999) / 1000
            if dist_km < 2:
                factors.append({"name": "Hospital nearby", "impact": +10, "detail": f"{dist_km:.1f}km away"})
            elif dist_km < 5:
                factors.append({"name": "Hospital accessible", "impact": +5, "detail": f"{dist_km:.1f}km away"})
            elif dist_km > 15:
                penalty = min(30, int(dist_km - 15) * 2)
                score -= penalty
                factors.append({"name": "Hospital far", "impact": -penalty, "detail": f"{dist_km:.1f}km away"})

        # Factor 2: Police presence
        police_results = [r for r in nearby_results if r.get("type") == "police"]
        if police_results:
            dist_km = police_results[0].get("distance_m", 99999) / 1000
            if dist_km < 3:
                factors.append({"name": "Police nearby", "impact": +8, "detail": f"{dist_km:.1f}km"})
            elif dist_km > 10:
                score -= 10
                factors.append({"name": "Police far", "impact": -10, "detail": f"{dist_km:.1f}km"})

    # Factor 3: Active road reports
    if reports:
        recent = [r for r in reports if r.get("age_min", 999) < 60]
        severe = [r for r in recent if r.get("type") in ["accident", "flooding"]]
        if severe:
            penalty = min(25, len(severe) * 10)
            score -= penalty
            factors.append({"name": "Active incidents", "impact": -penalty, "detail": f"{len(severe)} nearby"})
        elif recent:
            score -= 5
            factors.append({"name": "Minor issues", "impact": -5, "detail": f"{len(recent)} reports"})

    # Factor 4: Time of day risk
    hour = int(time.strftime("%H"))
    if 0 <= hour < 5:
        score -= 15
        factors.append({"name": "Late night", "impact": -15, "detail": "High risk hours"})
    elif 7 <= hour < 10 or 17 <= hour < 20:
        score -= 8
        factors.append({"name": "Rush hour", "impact": -8, "detail": "Peak traffic"})

    score = max(0, min(100, score))

    if score >= 80:
        level = "Safe"; color = "#43A047"
    elif score >= 60:
        level = "Moderate"; color = "#FF8F00"
    elif score >= 40:
        level = "Caution"; color = "#E65100"
    else:
        level = "Danger"; color = "#E53935"

    return {
        "score": score, "level": level, "color": color,
        "factors": factors,
        "recommendation": _get_recommendation(score, factors),
    }

def _get_recommendation(score, factors):
    if score >= 80: return "Area appears safe. Emergency services are accessible."
    if score >= 60: return "Exercise normal caution. Keep emergency numbers handy."
    if score >= 40: return "Increased risk detected. Drive carefully and stay alert."
    return "High risk area. Avoid if possible. Have 108 ready to call."
