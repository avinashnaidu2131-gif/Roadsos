"""
RoadSoS — Flask Application v3.0 (Real-Time + Responsive)
Run: python app.py
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import Config
import threading, time, json

app = Flask(__name__)
app.config.from_object(Config)
app.config["SECRET_KEY"] = Config.SECRET_KEY
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Pages ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/sos/<token>")
def sos_page(token):
    return render_template("sos_share.html", token=token)

@app.route("/map3d")
def map3d():
    return render_template("map3d.html")

# ── Health ─────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    from modules.realtime import get_client_count
    return jsonify({"status": "ok", "app": "RoadSoS", "version": "3.0",
                    "active_users": get_client_count()})

# ── Emergency Numbers ──────────────────────────────────────────────────────

@app.route("/api/emergency-numbers")
def emergency_numbers():
    from modules.emergency_numbers import get_quick_numbers
    country = request.args.get("country", "IN").upper()
    state   = request.args.get("state", "").upper() or None
    return jsonify(get_quick_numbers(country, state))

# ── Nearby Services ────────────────────────────────────────────────────────

@app.route("/api/nearby")
def nearby():
    lat          = request.args.get("lat", type=float)
    lon          = request.args.get("lon", type=float)
    service_type = request.args.get("type", "all")
    radius       = request.args.get("radius", type=int, default=Config.DEFAULT_RADIUS)
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400
    from modules.location_finder import find_nearby
    return jsonify(find_nearby(lat, lon, service_type, radius))

# ── Geocode ────────────────────────────────────────────────────────────────

@app.route("/api/geocode")
def geocode():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "q parameter required"}), 400
    from modules.location_finder import geocode_address
    result = geocode_address(query)
    if result:
        return jsonify({"lat": result[0], "lon": result[1], "query": query})
    return jsonify({"error": "Location not found"}), 404

# ── Chat (AI-powered) ──────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    data    = request.get_json() or {}
    message = data.get("message", "").strip()
    lat     = data.get("lat")
    lon     = data.get("lon")
    country = data.get("country", "IN").upper()
    state   = data.get("state", "").upper() or None
    if not message:
        return jsonify({"error": "message is required"}), 400

    from modules.ai_chat import ai_parse_intent
    from modules.multilingual import detect_language, translate
    from modules.location_finder import find_nearby, geocode_address
    from modules.response_builder import build_response

    lang   = detect_language(message)
    intent = ai_parse_intent(message)

    if intent["location_hint"] and not lat:
        coords = geocode_address(intent["location_hint"])
        if coords:
            lat, lon = coords

    if lat is None or lon is None:
        from modules.emergency_numbers import get_quick_numbers
        nums = get_quick_numbers(country, state)
        msg  = intent.get("ai_message") or translate("no_location", lang)
        return jsonify({
            "message": msg, "quick_numbers": nums.get("quick_numbers", {}),
            "results": [], "urgent_banner": intent["urgent"], "map_pins": [],
            "first_aid": intent.get("first_aid"), "lang": lang,
        })

    nearby_result = find_nearby(lat, lon, intent["service_type"])
    response      = build_response(intent, nearby_result, country, state, lang)
    if intent.get("ai_message"):
        response["ai_preamble"] = intent["ai_message"]
    if intent.get("first_aid"):
        response["first_aid"] = intent["first_aid"]
    response["lang"] = lang
    return jsonify(response)

# ── Heatmap ────────────────────────────────────────────────────────────────

@app.route("/api/heatmap")
def heatmap():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400
    from modules.accident_heatmap import get_heatmap_points
    points = get_heatmap_points(lat, lon)
    return jsonify({"points": points, "count": len(points)})

# ── Road Reports ───────────────────────────────────────────────────────────

@app.route("/api/reports", methods=["GET"])
def get_reports():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400
    from modules.road_reports import get_reports
    return jsonify({"reports": get_reports(lat, lon)})

@app.route("/api/reports", methods=["POST"])
def add_report():
    data = request.get_json() or {}
    from modules.road_reports import add_report
    result = add_report(data.get("lat"), data.get("lon"),
                        data.get("type"), data.get("description", ""))
    # Broadcast to nearby users via WebSocket
    if "error" not in result:
        from modules.realtime import broadcast_incident
        broadcast_incident(socketio, {**result, "lat": data.get("lat"), "lon": data.get("lon")})
    return jsonify(result)

@app.route("/api/reports/<int:report_id>/upvote", methods=["POST"])
def upvote_report(report_id):
    from modules.road_reports import upvote_report
    return jsonify(upvote_report(report_id))

# ── Hospital Beds ──────────────────────────────────────────────────────────

@app.route("/api/beds")
def hospital_beds():
    name = request.args.get("name", "")
    lat  = request.args.get("lat", type=float, default=0)
    if not name:
        return jsonify({"error": "name required"}), 400
    from modules.hospital_beds import get_bed_availability
    return jsonify(get_bed_availability(name, lat))

# ── SOS Share ──────────────────────────────────────────────────────────────

@app.route("/api/sos/create", methods=["POST"])
def create_sos():
    data = request.get_json() or {}
    lat  = data.get("lat")
    lon  = data.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat and lon required"}), 400
    from modules.sos_share import create_sos_link
    token    = create_sos_link(lat, lon, data.get("message",""), data.get("contact",""))
    base_url = request.host_url.rstrip("/")
    return jsonify({"token": token, "url": f"{base_url}/sos/{token}"})

@app.route("/api/sos/<token>")
def get_sos(token):
    from modules.sos_share import get_sos_data
    data = get_sos_data(token)
    if not data:
        return jsonify({"error": "SOS link not found"}), 404
    return jsonify(data)

# ── Language strings ───────────────────────────────────────────────────────

@app.route("/api/lang/<lang_code>")
def lang_strings(lang_code):
    from modules.multilingual import get_ui_strings, LANGUAGES
    if lang_code not in LANGUAGES:
        return jsonify({"error": "Unsupported language"}), 400
    return jsonify(get_ui_strings(lang_code))

# ── First Aid ──────────────────────────────────────────────────────────────

@app.route("/api/first-aid", methods=["POST"])
def first_aid():
    data    = request.get_json() or {}
    symptom = data.get("symptom", "").strip()
    lat     = data.get("lat")
    lon     = data.get("lon")
    if not symptom:
        return jsonify({"error": "symptom required"}), 400
    from modules.first_aid import get_first_aid
    return jsonify(get_first_aid(symptom, lat, lon))

# ── Live nearby refresh ────────────────────────────────────────────────────

@app.route("/api/live-nearby")
def live_nearby():
    """Fast endpoint for real-time refresh of nearby services."""
    lat  = request.args.get("lat", type=float)
    lon  = request.args.get("lon", type=float)
    stype= request.args.get("type", "hospital")
    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400
    from modules.location_finder import find_nearby
    result = find_nearby(lat, lon, stype, radius=3000)  # tighter radius for live
    return jsonify({
        "results": result.get("results", []),
        "timestamp": int(time.time()),
        "source": "live",
    })

# ── WebSocket Events ───────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    from modules.realtime import register_client, get_client_count
    register_client(request.sid)
    emit("connected", {
        "sid": request.sid,
        "active_users": get_client_count(),
        "message": "Connected to RoadSoS real-time server",
    })
    print(f"[WS] Client connected: {request.sid} | Total: {get_client_count()}")

@socketio.on("disconnect")
def on_disconnect():
    from modules.realtime import unregister_client, get_client_count
    unregister_client(request.sid)
    print(f"[WS] Client disconnected: {request.sid} | Total: {get_client_count()}")

@socketio.on("update_location")
def on_update_location(data):
    """Client sends GPS update — server refreshes nearby services and pushes back."""
    from modules.realtime import update_client_location
    lat = data.get("lat")
    lon = data.get("lon")
    if not lat or not lon:
        return
    update_client_location(request.sid, lat, lon)

    # Push fresh nearby data back to this client
    from modules.location_finder import find_nearby
    from modules.emergency_numbers import get_quick_numbers
    country = data.get("country", "IN")
    state   = data.get("state", "TG")

    nearby  = find_nearby(lat, lon, "hospital", radius=3000)
    numbers = get_quick_numbers(country, state)

    emit("location_updated", {
        "lat": lat, "lon": lon,
        "nearby_count": len(nearby.get("results", [])),
        "nearest": nearby.get("results", [{}])[0].get("name", ""),
        "nearest_dist": nearby.get("results", [{}])[0].get("distance_text", ""),
        "quick_numbers": numbers.get("quick_numbers", {}),
        "timestamp": int(time.time()),
    })

@socketio.on("report_incident")
def on_report_incident(data):
    """Client reports an incident — broadcast to nearby users."""
    from modules.road_reports import add_report
    from modules.realtime import broadcast_incident, get_client
    client = get_client(request.sid)
    lat = data.get("lat") or client.get("lat")
    lon = data.get("lon") or client.get("lon")
    if not lat or not lon:
        return
    result = add_report(lat, lon, data.get("type", "accident"), data.get("description", ""))
    if "error" not in result:
        broadcast_incident(socketio, {**result, "lat": lat, "lon": lon})
        emit("incident_reported", {"status": "ok", "id": result.get("id")})

@socketio.on("sos_alert")
def on_sos_alert(data):
    """Broadcast SOS alert to all connected users."""
    from modules.realtime import get_client
    client = get_client(request.sid)
    lat = data.get("lat") or client.get("lat")
    lon = data.get("lon") or client.get("lon")
    socketio.emit("sos_received", {
        "lat": lat, "lon": lon,
        "message": data.get("message", ""),
        "contact": data.get("contact", ""),
        "timestamp": int(time.time()),
    })

@socketio.on("ping_server")
def on_ping(data):
    emit("pong_server", {"ts": int(time.time()), "echo": data.get("ts")})

# ── Background: push live stats every 10s ─────────────────────────────────

def live_stats_broadcaster():
    """Background thread: push live stats to all clients every 10 seconds."""
    while True:
        time.sleep(10)
        from modules.realtime import get_client_count, get_all_clients
        from modules.road_reports import get_reports
        count = get_client_count()
        if count == 0:
            continue
        # Push to each client based on their location
        for sid, info in get_all_clients():
            lat = info.get("lat")
            lon = info.get("lon")
            if not lat or not lon:
                continue
            try:
                reports = get_reports(lat, lon, radius_km=5)
                socketio.emit("live_stats", {
                    "active_users": count,
                    "nearby_incidents": len(reports),
                    "timestamp": int(time.time()),
                }, to=sid)
            except Exception:
                pass

_stats_thread = threading.Thread(target=live_stats_broadcaster, daemon=True)
_stats_thread.start()


# ── Safety Score ───────────────────────────────────────────────────────────────

@app.route("/api/safety-score")
def safety_score():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400
    from modules.location_finder import find_nearby
    from modules.road_reports import get_reports
    from modules.safety_score import get_safety_score
    from modules.coverage_gap import analyze_coverage
    nearby = find_nearby(lat, lon, "all", radius=5000)
    all_results = []
    if nearby.get("type") == "all":
        for lst in nearby.get("results", {}).values():
            all_results.extend(lst)
    reports = get_reports(lat, lon, radius_km=3)
    safety  = get_safety_score(lat, lon, all_results, reports)
    coverage= analyze_coverage(lat, lon, all_results)
    safety["gaps"] = coverage["gaps"]
    safety["coverage_score"] = coverage["coverage_score"]
    return jsonify(safety)

# ── Impact Analytics ───────────────────────────────────────────────────────────

@app.route("/api/impact")
def impact():
    from modules.impact_analytics import get_impact_stats
    return jsonify(get_impact_stats())

# ── APK Download Page ──────────────────────────────────────────────────────
@app.route('/download')
def download_page():
    import os
    apk_path = os.path.join(app.root_path, 'static', 'downloads', 'app-debug.apk')
    if os.path.exists(apk_path):
        size_bytes = os.path.getsize(apk_path)
        size_mb = round(size_bytes / (1024 * 1024), 1)
        apk_size = f"{size_mb} MB"
    else:
        apk_size = "~9 MB"
    return render_template('download.html', apk_size=apk_size)

@app.route('/download/apk')
def download_apk():
    import os
    from flask import send_from_directory, abort
    apk_dir  = os.path.join(app.root_path, 'static', 'downloads')
    apk_file = 'app-debug.apk'
    apk_path = os.path.join(apk_dir, apk_file)
    if not os.path.exists(apk_path):
        abort(404, description="APK not yet available. Check back after the GitHub Actions build completes.")
    return send_from_directory(
        apk_dir, apk_file,
        as_attachment=True,
        download_name='RoadSoS.apk',
        mimetype='application/vnd.android.package-archive'
    )

# ── Web Share Target — PWA "Share" from other apps ────────────────────────
# manifest.json share_target.action = "/share"
# Android/iOS sends: GET /share?title=...&text=...&url=...
# We forward to the main app which already handles SOS and location sharing.
@app.route('/share')
def share_target():
    from flask import request, redirect
    title = request.args.get('title', '')
    text  = request.args.get('text', '')
    url   = request.args.get('url', '')
    # Build a pre-filled chat query from the shared content
    query = text or title or url or ''
    import urllib.parse
    return redirect(f'/?shared={urllib.parse.quote(query)}')

# ── Digital Asset Links — TWA verification ─────────────────────────────────
# Must be BEFORE __main__ guard so it registers under gunicorn / any WSGI host

@app.route('/.well-known/assetlinks.json')
def asset_links():
    from flask import send_from_directory
    import os
    return send_from_directory(
        os.path.join(app.root_path, 'static', '.well-known'),
        'assetlinks.json',
        mimetype='application/json'
    )

# ── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 RoadSoS v3.0 — Real-Time Server starting...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=Config.DEBUG, allow_unsafe_werkzeug=True)
