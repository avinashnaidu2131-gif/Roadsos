"""
RoadSoS — Multilingual Module
Supports English, Telugu, Hindi, Tamil.
"""

LANGUAGES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
}

# UI strings per language
STRINGS = {
    "en": {
        "greeting": "Hi! I'm RoadSoS — your road emergency assistant.",
        "try_asking": "Try asking:",
        "nearest_hospital": "nearest hospital",
        "call_police": "call police",
        "car_broke_down": "car broke down",
        "need_ambulance": "need ambulance now",
        "describe": "Describe your emergency...",
        "found": "Found {count} {type}(s) near you. Nearest: {name} ({dist})",
        "no_location": "I need your location to find nearby services. Please enable GPS or type a location.",
        "emergency": "EMERGENCY",
        "quick_dial": "Quick Dial",
        "directions": "Directions",
        "call": "Call",
        "map": "Map",
        "works_offline": "OpenStreetMap · Works offline · 30+ countries",
    },
    "te": {
        "greeting": "నమస్కారం! నేను RoadSoS — మీ రహదారి అత్యవసర సహాయకుడు.",
        "try_asking": "ఇలా అడగండి:",
        "nearest_hospital": "దగ్గరలో ఆసుపత్రి",
        "call_police": "పోలీసులను పిలవండి",
        "car_broke_down": "కారు పాడైంది",
        "need_ambulance": "ఇప్పుడే అంబులెన్స్ కావాలి",
        "describe": "మీ అత్యవసర స్థితిని వివరించండి...",
        "found": "మీ దగ్గర {count} {type} కనుగొనబడ్డాయి. సమీపంగా: {name} ({dist})",
        "no_location": "సమీప సేవలను కనుగొనడానికి మీ స్థానం అవసరం. GPS ఆన్ చేయండి.",
        "emergency": "అత్యవసరం",
        "quick_dial": "త్వరిత డయల్",
        "directions": "దిశలు",
        "call": "కాల్",
        "map": "మ్యాప్",
        "works_offline": "OpenStreetMap · ఆఫ్‌లైన్‌లో పని చేస్తుంది · 30+ దేశాలు",
    },
    "hi": {
        "greeting": "नमस्ते! मैं RoadSoS हूं — आपका सड़क आपातकालीन सहायक।",
        "try_asking": "पूछें:",
        "nearest_hospital": "नजदीकी अस्पताल",
        "call_police": "पुलिस को बुलाएं",
        "car_broke_down": "कार खराब हो गई",
        "need_ambulance": "अभी एम्बुलेंस चाहिए",
        "describe": "अपनी आपात स्थिति बताएं...",
        "found": "आपके पास {count} {type} मिले। निकटतम: {name} ({dist})",
        "no_location": "पास की सेवाएं खोजने के लिए आपका स्थान चाहिए। GPS चालू करें।",
        "emergency": "आपातकाल",
        "quick_dial": "त्वरित डायल",
        "directions": "दिशाएं",
        "call": "कॉल",
        "map": "मानचित्र",
        "works_offline": "OpenStreetMap · ऑफलाइन काम करता है · 30+ देश",
    },
    "ta": {
        "greeting": "வணக்கம்! நான் RoadSoS — உங்கள் சாலை அவசர உதவியாளர்.",
        "try_asking": "கேளுங்கள்:",
        "nearest_hospital": "அருகில் உள்ள மருத்துவமனை",
        "call_police": "காவலரை அழைக்கவும்",
        "car_broke_down": "கார் கேடாகிவிட்டது",
        "need_ambulance": "இப்போது ஆம்புலன்ஸ் வேண்டும்",
        "describe": "உங்கள் அவசரநிலையை விவரிக்கவும்...",
        "found": "உங்களுக்கு அருகில் {count} {type} கண்டறியப்பட்டது. அருகில்: {name} ({dist})",
        "no_location": "அருகில் உள்ள சேவைகளைக் கண்டறிய உங்கள் இருப்பிடம் தேவை. GPS இயக்கவும்.",
        "emergency": "அவசரநிலை",
        "quick_dial": "விரைவு டயல்",
        "directions": "திசைகள்",
        "call": "அழைப்பு",
        "map": "வரைபடம்",
        "works_offline": "OpenStreetMap · ஆஃப்லைனில் செயல்படும் · 30+ நாடுகள்",
    },
}

# Telugu, Hindi, Tamil script detection
TELUGU_RANGE  = (0x0C00, 0x0C7F)
HINDI_RANGE   = (0x0900, 0x097F)
TAMIL_RANGE   = (0x0B80, 0x0BFF)


def detect_language(text: str) -> str:
    """Detect language from script. Defaults to English."""
    for ch in text:
        cp = ord(ch)
        if TELUGU_RANGE[0] <= cp <= TELUGU_RANGE[1]: return "te"
        if HINDI_RANGE[0]  <= cp <= HINDI_RANGE[1]:  return "hi"
        if TAMIL_RANGE[0]  <= cp <= TAMIL_RANGE[1]:  return "ta"
    return "en"


def translate(key: str, lang: str = "en", **kwargs) -> str:
    """Get a translated string."""
    lang = lang if lang in STRINGS else "en"
    s = STRINGS[lang].get(key, STRINGS["en"].get(key, key))
    if kwargs:
        try: s = s.format(**kwargs)
        except: pass
    return s


def get_ui_strings(lang: str) -> dict:
    """Return all UI strings for a language."""
    return STRINGS.get(lang, STRINGS["en"])


def get_service_name(service_type: str, lang: str) -> str:
    names = {
        "en": {"hospital":"hospital","police":"police","ambulance":"ambulance","towing":"towing service","fire":"fire station"},
        "te": {"hospital":"ఆసుపత్రి","police":"పోలీస్","ambulance":"అంబులెన్స్","towing":"టోయింగ్","fire":"అగ్నిమాపక"},
        "hi": {"hospital":"अस्पताल","police":"पुलिस","ambulance":"एम्बुलेंस","towing":"टोइंग","fire":"अग्निशमन"},
        "ta": {"hospital":"மருத்துவமனை","police":"காவல்","ambulance":"ஆம்புலன்ஸ்","towing":"டோயிங்","fire":"தீயணைப்பு"},
    }
    return names.get(lang, names["en"]).get(service_type, service_type)
