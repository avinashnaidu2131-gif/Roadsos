"""
RoadSoS — AI Chat Module
Uses Groq API (free, fast) for intelligent intent parsing.
Falls back to keyword parser if API unavailable.
Supports both Groq and Anthropic keys — whichever is set.
"""

import os
import json
import requests
from modules.intent_parser import parse_intent as keyword_parse

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
ANTHROPIC_API_KEY= os.environ.get("ANTHROPIC_API_KEY", "")

GROQ_MODEL       = "llama-3.1-8b-instant"      # free, very fast
GROQ_URL         = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are RoadSoS, an AI road emergency assistant.
Your job is to understand what emergency help the user needs and extract structured information.

Always respond with ONLY a valid JSON object — no markdown, no explanation, no extra text:
{
  "service_type": "hospital" | "police" | "ambulance" | "towing" | "fire" | "all",
  "location_hint": "place name if mentioned, else null",
  "urgent": true | false,
  "use_gps": true | false,
  "ai_message": "A helpful 1-2 sentence response to the user in their language",
  "first_aid": "If physical injury mentioned, give 2-3 brief first aid steps. Else null.",
  "language": "en" | "te" | "hi" | "ta"
}

Rules:
- service_type: pick the most relevant emergency service
- urgent: true if user says help/emergency/now/critical/dying/SOS/accident
- ai_message: calm, reassuring, action-oriented. Mention emergency number if urgent.
- first_aid: ONLY for physical injuries like bleeding, fracture, burns, unconscious
- language: detect from script — Telugu=te, Hindi=hi, Tamil=ta, else en
- Respond ONLY with the JSON. No markdown fences."""


def ai_parse_intent(message: str) -> dict:
    """
    Parse intent using Groq (primary) or Anthropic (fallback).
    Falls back to keyword parser if neither key is set or API fails.
    """
    if GROQ_API_KEY:
        return _call_groq(message)
    elif ANTHROPIC_API_KEY:
        return _call_anthropic(message)
    else:
        return _keyword_fallback(message)


def _call_groq(message: str) -> dict:
    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": message},
                ],
                "max_tokens": 300,
                "temperature": 0.1,
            },
            timeout=8,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        return _parse_json_response(raw, message)

    except Exception as e:
        print(f"[Groq] Error: {e} — falling back to keywords")
        return _keyword_fallback(message)


def _call_anthropic(message: str) -> dict:
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 300,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": message}],
            },
            timeout=8,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        return _parse_json_response(raw, message)

    except Exception as e:
        print(f"[Anthropic] Error: {e} — falling back to keywords")
        return _keyword_fallback(message)


def _parse_json_response(raw: str, original_message: str) -> dict:
    """Parse JSON from AI response, stripping markdown fences if present."""
    # Strip markdown fences
    if "```" in raw:
        parts = raw.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"): p = p[4:].strip()
            if p.startswith("{"): raw = p; break

    parsed = json.loads(raw.strip())
    return {
        "service_type":  parsed.get("service_type", "all"),
        "location_hint": parsed.get("location_hint"),
        "urgent":        bool(parsed.get("urgent", False)),
        "use_gps":       bool(parsed.get("use_gps", True)),
        "ai_message":    parsed.get("ai_message"),
        "first_aid":     parsed.get("first_aid"),
        "language":      parsed.get("language", "en"),
        "raw":           original_message,
    }


def _keyword_fallback(message: str) -> dict:
    result = keyword_parse(message)
    result["ai_message"] = None
    result["first_aid"]  = None
    result["language"]   = "en"
    return result