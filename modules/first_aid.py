"""
RoadSoS — First Aid Module
Uses Groq/Anthropic AI for symptom-specific first aid.
Falls back to built-in database if API unavailable.
"""

import os, requests, json

GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

FIRST_AID_PROMPT = """You are an emergency first aid assistant. 
Given a symptom or injury, provide clear, numbered first aid steps.

Respond ONLY with a JSON object:
{
  "steps": ["Step 1 text", "Step 2 text", "Step 3 text", "Step 4 text"],
  "call_number": "108",
  "warning": "Any critical warning or null"
}

Rules:
- 3-5 clear, actionable steps. Short sentences.
- Always include calling emergency services as one step.
- call_number: always "108" for India
- warning: critical caution if needed (e.g. "Do NOT move if spinal injury suspected")
- Respond ONLY with JSON. No markdown."""

# Built-in fallback database
BUILTIN = {
    "bleeding": {
        "steps": [
            "Apply firm pressure directly on the wound with a clean cloth or bandage",
            "Keep continuous pressure — do not remove cloth even if soaked, add more on top",
            "Elevate the injured area above heart level if possible",
            "Call 108 immediately for severe bleeding",
        ],
        "call_number": "108",
        "warning": "Do NOT use a tourniquet unless bleeding is life-threatening and uncontrolled"
    },
    "fracture": {
        "steps": [
            "Do NOT try to straighten or move the broken bone",
            "Immobilise the injured area with improvised splint (sticks, rolled newspaper)",
            "Apply ice pack wrapped in cloth to reduce swelling — 20 min on, 20 min off",
            "Keep the person still and call 108 for transport",
        ],
        "call_number": "108",
        "warning": "If spine/neck fracture suspected — do NOT move the person at all"
    },
    "unconscious": {
        "steps": [
            "Check responsiveness — tap shoulders and shout 'Are you okay?'",
            "If not breathing, start CPR — 30 chest compressions then 2 rescue breaths",
            "Place in recovery position if breathing (on side, head tilted back)",
            "Call 108 immediately and stay with the person",
        ],
        "call_number": "108",
        "warning": "Never give water or food to an unconscious person"
    },
    "burns": {
        "steps": [
            "Cool the burn immediately with cool (not cold) running water for 10-20 minutes",
            "Remove jewellery and clothing near the burn — but NOT if stuck to skin",
            "Cover loosely with cling film or a clean non-fluffy material",
            "Call 108 for severe burns or burns to face/hands/genitals",
        ],
        "call_number": "108",
        "warning": "Do NOT use ice, butter, toothpaste or any cream on burns"
    },
    "chest pain": {
        "steps": [
            "Have the person sit or lie down in a comfortable position — loosen tight clothing",
            "If conscious and not allergic: give aspirin 325mg to chew (not swallow whole)",
            "Keep the person calm and still — reassure them help is coming",
            "Call 108 immediately — do not drive to hospital yourself",
        ],
        "call_number": "108",
        "warning": "Do NOT leave the person alone. If they lose consciousness, start CPR"
    },
    "head injury": {
        "steps": [
            "Keep the person still — do not move if spinal injury possible",
            "Apply gentle pressure on any wound with clean cloth to control bleeding",
            "Do NOT remove any object embedded in the skull",
            "Monitor for confusion, vomiting, or loss of consciousness — call 108 immediately",
        ],
        "call_number": "108",
        "warning": "Any loss of consciousness after head injury = medical emergency. Call 108 now."
    },
    "spinal": {
        "steps": [
            "Do NOT move the person — keep them completely still",
            "Support head and neck in the position found — do not straighten",
            "If they must be moved (fire/water danger), use log-roll technique with helpers",
            "Call 108 immediately and inform about possible spinal injury",
        ],
        "call_number": "108",
        "warning": "CRITICAL: Moving a spinal injury patient incorrectly can cause permanent paralysis"
    },
    "default": {
        "steps": [
            "Keep the person calm and still in a safe location",
            "Check for breathing and consciousness",
            "Apply pressure to any bleeding wounds with clean cloth",
            "Call 108 for emergency medical assistance immediately",
        ],
        "call_number": "108",
        "warning": None
    }
}


def get_first_aid(symptom: str, lat=None, lon=None) -> dict:
    """Get AI-powered first aid steps for a symptom."""
    if GROQ_API_KEY:
        result = _call_groq(symptom)
        if result: return result
    elif ANTHROPIC_API_KEY:
        result = _call_anthropic(symptom)
        if result: return result
    return _builtin_fallback(symptom)


def _call_groq(symptom: str) -> dict:
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": FIRST_AID_PROMPT},
                    {"role": "user",   "content": f"Injury/symptom: {symptom}"},
                ],
                "max_tokens": 400, "temperature": 0.1,
            },
            timeout=8,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        return _parse(raw)
    except Exception as e:
        print(f"[FirstAid Groq] {e}")
        return None


def _call_anthropic(symptom: str) -> dict:
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 400, "system": FIRST_AID_PROMPT,
                  "messages": [{"role": "user", "content": f"Injury/symptom: {symptom}"}]},
            timeout=8,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        return _parse(raw)
    except Exception as e:
        print(f"[FirstAid Anthropic] {e}")
        return None


def _parse(raw: str) -> dict:
    if "```" in raw:
        for p in raw.split("```"):
            p = p.strip()
            if p.startswith("json"): p = p[4:].strip()
            if p.startswith("{"): raw = p; break
    parsed = json.loads(raw.strip())
    return {
        "steps":       parsed.get("steps", []),
        "call_number": parsed.get("call_number", "108"),
        "warning":     parsed.get("warning"),
    }


def _builtin_fallback(symptom: str) -> dict:
    s = symptom.lower()
    for key, data in BUILTIN.items():
        if key in s:
            return data
    return BUILTIN["default"]
