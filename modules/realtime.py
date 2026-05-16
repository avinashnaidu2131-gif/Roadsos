"""
RoadSoS — Real-Time Module
WebSocket-based live updates:
- GPS position tracking (every 5s)
- Live nearby service refresh (every 30s)
- Crowdsourced incident broadcasts
- Live emergency number push by detected country
"""

import time
import threading
import math

# Store connected clients: {sid: {lat, lon, country, state}}
_clients = {}
_lock = threading.Lock()

def register_client(sid, lat=None, lon=None, country="IN", state=None):
    with _lock:
        _clients[sid] = {
            "lat": lat, "lon": lon,
            "country": country, "state": state,
            "connected_at": time.time(),
            "last_update": time.time(),
        }

def update_client_location(sid, lat, lon):
    with _lock:
        if sid in _clients:
            _clients[sid]["lat"] = lat
            _clients[sid]["lon"] = lon
            _clients[sid]["last_update"] = time.time()

def unregister_client(sid):
    with _lock:
        _clients.pop(sid, None)

def get_client(sid):
    with _lock:
        return _clients.get(sid, {}).copy()

def get_all_clients():
    with _lock:
        return list(_clients.items())

def get_client_count():
    with _lock:
        return len(_clients)

def broadcast_incident(socketio, incident_data):
    """Broadcast a new road incident to all nearby clients."""
    inc_lat = incident_data.get("lat", 0)
    inc_lon = incident_data.get("lon", 0)
    for sid, info in get_all_clients():
        if info.get("lat") and info.get("lon"):
            dist = _dist_km(info["lat"], info["lon"], inc_lat, inc_lon)
            if dist <= 15:  # Only notify clients within 15km
                socketio.emit("incident_nearby", {
                    "incident": incident_data,
                    "distance_km": round(dist, 1),
                }, to=sid)

def _dist_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
