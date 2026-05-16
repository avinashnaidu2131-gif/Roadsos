"""
RoadSoS — Emergency Numbers Module
Provides lookup functions for emergency contact numbers
by country code and Indian state code.
"""

import json
import os

# Load the database once at import time
_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'emergency_numbers.json')

with open(_DB_PATH, 'r', encoding='utf-8') as f:
    _DB = json.load(f)

COUNTRIES = _DB['countries']


def get_numbers_by_country(country_code: str, state_code: str = None) -> dict:
    """
    Returns emergency numbers for a country (and optionally an Indian state).

    Args:
        country_code: ISO 3166-1 alpha-2 code e.g. 'IN', 'US', 'GB'
        state_code:   Indian state code e.g. 'TG', 'KA', 'MH' (only used when country_code='IN')

    Returns:
        dict with keys: country, state (if applicable), numbers, source
    """
    country_code = country_code.upper().strip()
    country = COUNTRIES.get(country_code)

    if not country:
        return {
            'found': False,
            'message': f"No data for country code '{country_code}'",
            'fallback': 'Try dialling 112 — it works in most countries as a universal emergency number.'
        }

    result = {
        'found': True,
        'country': country['name'],
        'continent': country.get('continent', 'Unknown'),
        'numbers': {},
        'state': None
    }

    # India: check for state-level numbers
    if country_code == 'IN' and state_code:
        state_code = state_code.upper().strip()
        state = country.get('states', {}).get(state_code)
        if state:
            result['state'] = state.get('name')
            result['numbers'] = {
                'police':        state.get('police', country['national'].get('police')),
                'ambulance':     state.get('ambulance', country['national'].get('ambulance')),
                'fire':          state.get('fire', country['national'].get('fire')),
                'emergency':     state.get('emergency', country['national'].get('emergency')),
                'traffic_police': state.get('traffic_police'),
                'highway_patrol': state.get('highway_patrol', country['national'].get('highway_patrol')),
                'women_safety':  state.get('women_safety'),
                'child_helpline': state.get('child_helpline'),
                'tourist_police': state.get('tourist_police'),
                'local_police_control': state.get('local_police_control'),
            }
            # Remove None values
            result['numbers'] = {k: v for k, v in result['numbers'].items() if v}
            return result

    # Fallback to national numbers
    result['numbers'] = {k: v for k, v in country['national'].items() if v and k != 'note'}
    result['note'] = country['national'].get('note')
    return result


def get_quick_numbers(country_code: str, state_code: str = None) -> dict:
    """
    Returns only the most critical numbers: police, ambulance, emergency.
    Good for the chatbot's instant response card.
    """
    data = get_numbers_by_country(country_code, state_code)
    if not data.get('found'):
        return data

    quick = {}
    for key in ['emergency', 'police', 'ambulance', 'fire']:
        if key in data['numbers']:
            quick[key] = data['numbers'][key]

    return {
        'found': True,
        'country': data['country'],
        'state': data.get('state'),
        'quick_numbers': quick,
        'all_numbers': data['numbers']
    }


def get_all_supported_countries() -> list:
    """Returns a list of all supported countries with their codes."""
    return [
        {'code': code, 'name': info['name'], 'continent': info.get('continent', 'Unknown')}
        for code, info in COUNTRIES.items()
        if code != 'EU'
    ]


def get_india_states() -> list:
    """Returns a list of all supported Indian states."""
    india = COUNTRIES.get('IN', {})
    return [
        {'code': code, 'name': info['name'], 'capital': info.get('capital', '')}
        for code, info in india.get('states', {}).items()
    ]


def search_country_by_name(query: str) -> list:
    """
    Fuzzy-ish search: returns countries whose name contains the query string.
    Used when the user types a country name instead of a code.
    """
    query = query.lower().strip()
    matches = []
    for code, info in COUNTRIES.items():
        if query in info['name'].lower():
            matches.append({'code': code, 'name': info['name']})
    return matches


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=== Telangana (IN/TG) ===")
    result = get_quick_numbers('IN', 'TG')
    for k, v in result['quick_numbers'].items():
        print(f"  {k:15}: {v}")

    print("\n=== Maharashtra (IN/MH) ===")
    result = get_numbers_by_country('IN', 'MH')
    for k, v in result['numbers'].items():
        print(f"  {k:25}: {v}")

    print("\n=== United Kingdom ===")
    result = get_quick_numbers('GB')
    for k, v in result['quick_numbers'].items():
        print(f"  {k:15}: {v}")

    print("\n=== UAE ===")
    result = get_quick_numbers('AE')
    for k, v in result['quick_numbers'].items():
        print(f"  {k:15}: {v}")

    print("\n=== Unknown country ===")
    print(get_quick_numbers('XX'))

    print(f"\n=== Supported countries: {len(get_all_supported_countries())} ===")
    print(f"=== Supported Indian states: {len(get_india_states())} ===")

    print("\n=== Search: 'nig' ===")
    print(search_country_by_name('nig'))
