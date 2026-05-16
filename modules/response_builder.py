"""
RoadSoS — Response Builder (multilingual)
"""
from modules.emergency_numbers import get_quick_numbers
from modules.multilingual import translate, get_service_name

def build_response(intent, nearby, country="IN", state=None, lang="en"):
    service_type = intent["service_type"]
    urgent       = intent["urgent"]
    numbers      = get_quick_numbers(country, state)

    if nearby.get("error"):
        return {
            "message": f"Sorry, I couldn't find that. {nearby['error']}",
            "quick_numbers": numbers.get("quick_numbers", {}),
            "results": [], "urgent_banner": urgent, "map_pins": [],
        }

    results = _flatten(nearby)
    if not results:
        msg = translate("no_location", lang)
    elif urgent:
        msg = _urgent_msg(service_type, results, numbers, lang)
    else:
        msg = _normal_msg(service_type, results, lang)

    map_pins = [{"lat":r["lat"],"lon":r["lon"],"name":r["name"],
                 "type":r["type"],"distance_text":r["distance_text"]} for r in results]
    return {
        "message": msg,
        "quick_numbers": numbers.get("quick_numbers", {}),
        "results": results, "urgent_banner": urgent, "map_pins": map_pins,
    }

def _flatten(nearby):
    if nearby.get("type") == "all":
        items = []
        for lst in nearby.get("results", {}).values(): items.extend(lst)
        items.sort(key=lambda x: x["distance_m"])
        return items
    return nearby.get("results", [])

def _urgent_msg(service_type, results, numbers, lang):
    top  = results[0]
    nums = numbers.get("quick_numbers", {})
    call = ""
    if service_type == "ambulance" and nums.get("ambulance"):
        call = f" CALL {nums['ambulance']} NOW."
    elif service_type == "police" and nums.get("police"):
        call = f" CALL POLICE {nums['police']} NOW."
    elif nums.get("emergency"):
        call = f" Emergency: {nums['emergency']}"
    svc = get_service_name(service_type, lang)
    return f"EMERGENCY — nearest {svc}: {top['name']} ({top['distance_text']} away).{call}"

def _normal_msg(service_type, results, lang):
    top   = results[0]
    svc   = get_service_name(service_type, lang)
    msg   = translate("found", lang, count=len(results), type=svc,
                      name=top["name"], dist=top["distance_text"])
    if top.get("phone"):
        msg += f" — {top['phone'].split(';')[0].strip()}"
    return msg
