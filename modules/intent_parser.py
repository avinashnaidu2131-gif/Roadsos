"""
RoadSoS — Intent Parser
Extracts service_type and location_hint from plain-text user messages.
No ML model needed — keyword matching is fast, offline, and sufficient.
"""

import re

# Keywords mapped to service types
INTENT_MAP = {
    "hospital": [
        "hospital", "doctor", "clinic", "medical", "injury", "hurt",
        "injured", "bleeding", "trauma", "icu", "emergency room", "er",
        "healthcare", "health centre", "nursing"
    ],
    "police": [
        "police", "cop", "officer", "thana", "pcr", "fir", "theft",
        "accident report", "crime", "law enforcement", "constable"
    ],
    "ambulance": [
        "ambulance", "108", "paramedic", "ems", "life support",
        "critical", "unconscious", "not breathing", "cardiac"
    ],
    "towing": [
        "tow", "towing", "breakdown", "broke down", "broken down",
        "car broke", "vehicle broke", "engine stalled",
        "puncture", "flat tyre", "flat tire",
        "stuck", "stranded", "mechanic", "car repair", "vehicle repair",
        "spare", "jump start", "battery dead"
    ],
    "fire": [
        "fire", "flames", "burning", "smoke", "fire station",
        "firefighter", "blaze"
    ],
}

# Phrases that mean "near me / my location"
NEAR_ME_PHRASES = [
    "near me", "nearby", "closest", "nearest", "around me",
    "here", "my location", "current location", "where i am"
]

# Urgency signals
URGENT_PHRASES = [
    "help", "emergency", "urgent", "sos", "asap", "now",
    "immediately", "dying", "critical", "quick", "fast"
]

# Words that precede "near" but are service-type words, not location words
LOCATION_STRIP_PREFIXES = re.compile(
    r"^(tyre|tire|engine|car|vehicle|road|highway|towing|police|hospital|ambulance|fire)\s+",
    re.IGNORECASE
)


def parse_intent(message: str) -> dict:
    """
    Returns:
    {
        service_type: str | "all",
        location_hint: str | None,
        use_gps: bool,
        urgent: bool,
        raw: str
    }
    """
    text = message.lower().strip()

    service_type = _extract_service(text)
    location_hint = _extract_location(message)
    use_gps = any(phrase in text for phrase in NEAR_ME_PHRASES)
    urgent = any(phrase in text for phrase in URGENT_PHRASES)

    return {
        "service_type": service_type,
        "location_hint": location_hint,
        "use_gps": use_gps or (location_hint is None),
        "urgent": urgent,
        "raw": message,
    }


def _extract_service(text: str) -> str:
    scores = {stype: 0 for stype in INTENT_MAP}
    for stype, keywords in INTENT_MAP.items():
        for kw in keywords:
            if kw in text:
                scores[stype] += 1

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "all"
    return best


def _extract_location(text: str) -> str | None:
    """
    Extracts address/place hint from phrases like:
    "hospital near Banjara Hills" / "police at Jubilee Hills" / "near HITEC City"
    """
    pattern = r"\b(?:near|at|around|in|close to|beside|next to)\b\s+([A-Za-z0-9][A-Za-z0-9\s,.-]{2,55})"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None

    hint = match.group(1).strip()
    # Strip leading service-type words that got captured (e.g. "tyre near Jubilee")
    hint = LOCATION_STRIP_PREFIXES.sub("", hint).strip()
    # Strip trailing noise words
    hint = re.sub(r"\s*,?\s*(need|please|help|now|asap|quickly).*$", "", hint, flags=re.IGNORECASE).strip()
    # Don't return generic phrases
    if any(p in hint.lower() for p in ["me", "here", "my location"]):
        return None
    return hint if len(hint) >= 3 else None


# Quick self-test
if __name__ == "__main__":
    tests = [
        ("nearest hospital near me",           "hospital",  None),
        ("my car broke down near HITEC City",   "towing",    "HITEC City"),
        ("flat tyre near Jubilee Hills",         "towing",    "Jubilee Hills"),
        ("help ambulance now",                  "ambulance", None),
        ("police station",                      "police",    None),
        ("hospital near Banjara Hills",         "hospital",  "Banjara Hills"),
        ("nearest fire station near Gachibowli","fire",      "Gachibowli"),
    ]
    all_pass = True
    for msg, exp_svc, exp_loc in tests:
        r = parse_intent(msg)
        ok = r["service_type"] == exp_svc and r["location_hint"] == exp_loc
        print(f"{'✅' if ok else '❌'} [{r['service_type']:10}] loc={r['location_hint']}  ← \"{msg}\"")
        if not ok:
            print(f"   EXPECTED: service={exp_svc} loc={exp_loc}")
            all_pass = False
    print("\nAll tests passed! ✅" if all_pass else "\nSOME TESTS FAILED ❌")
