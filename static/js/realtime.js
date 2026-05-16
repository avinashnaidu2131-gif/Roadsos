// RoadSoS — Real-Time Module v3.0
// WebSocket client: live GPS tracking, nearby refresh, incident broadcasts

const RT = {
  socket: null,
  connected: false,
  reconnectDelay: 2000,
  locationInterval: null,
  refreshInterval: null,
  lastLat: null,
  lastLon: null,
  activeUsers: 0,
};

// ── Init ───────────────────────────────────────────────────────────────────
window.initRealTime = function() {
  loadSocketIO(() => {
    connectSocket();
    startLocationTracking();
    startNearbyRefresh();
  });
};

function loadSocketIO(cb) {
  if (window.io) { cb(); return; }
  const s = document.createElement("script");
  s.src = "https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js";
  s.onload = cb;
  s.onerror = () => console.warn("[RT] Socket.IO CDN failed — real-time disabled");
  document.head.appendChild(s);
}

// ── Connection ─────────────────────────────────────────────────────────────
function connectSocket() {
  if (!window.io) return;
  try {
    RT.socket = io(window.location.origin, {
      transports: ["websocket", "polling"],
      reconnectionDelay: RT.reconnectDelay,
      reconnectionAttempts: 10,
    });

    RT.socket.on("connect", () => {
      RT.connected = true;
      setRTStatus("connected", "Live");
      console.log("[RT] Connected:", RT.socket.id);
      // Send current location immediately
      if (window.userLat && window.userLon) {
        sendLocation(window.userLat, window.userLon);
      }
    });

    RT.socket.on("disconnect", () => {
      RT.connected = false;
      setRTStatus("disconnected", "Reconnecting...");
    });

    RT.socket.on("connect_error", () => {
      setRTStatus("connecting", "Connecting...");
    });

    RT.socket.on("connected", data => {
      RT.activeUsers = data.active_users || 0;
      updateRTStats();
    });

    RT.socket.on("location_updated", data => {
      updateRTStats(data);
      // Update nearby badge
      const badge = document.getElementById("rt-nearby-badge");
      if (badge && data.nearest) {
        badge.textContent = `📍 ${data.nearest} · ${data.nearest_dist}`;
        badge.classList.remove("updating");
      }
    });

    RT.socket.on("live_stats", data => {
      RT.activeUsers = data.active_users || 0;
      updateRTStats(data);
    });

    RT.socket.on("incident_nearby", data => {
      showIncidentToast(data);
    });

    RT.socket.on("sos_received", data => {
      showSOSAlert(data);
    });

    RT.socket.on("pong_server", data => {
      const latency = Date.now() - (data.echo || Date.now());
      const el = document.getElementById("rt-latency");
      if (el) el.textContent = `${latency}ms`;
    });

  } catch(e) {
    console.warn("[RT] Socket init failed:", e);
  }
}

// ── Location tracking ──────────────────────────────────────────────────────
function startLocationTracking() {
  // Watch GPS position continuously
  if (!navigator.geolocation) return;
  navigator.geolocation.watchPosition(
    pos => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      const moved = !RT.lastLat || distance(lat, lon, RT.lastLat, RT.lastLon) > 0.05; // 50m threshold
      RT.lastLat = lat;
      RT.lastLon = lon;
      window.userLat = lat;
      window.userLon = lon;
      if (moved && RT.connected && RT.socket) {
        sendLocation(lat, lon);
      }
    },
    err => console.warn("[RT] GPS watch error:", err.message),
    { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
  );

  // Also push location every 15s even if not moved (keepalive)
  RT.locationInterval = setInterval(() => {
    if (window.userLat && window.userLon && RT.connected && RT.socket) {
      RT.socket.emit("ping_server", { ts: Date.now() });
      sendLocation(window.userLat, window.userLon);
    }
  }, 15000);
}

function sendLocation(lat, lon) {
  if (!RT.socket || !RT.connected) return;
  RT.socket.emit("update_location", {
    lat, lon,
    country: window.currentCountry || "IN",
    state: window.currentState || "TG",
  });
}

// ── Live nearby refresh ────────────────────────────────────────────────────
function startNearbyRefresh() {
  // Refresh nearby services every 30s
  RT.refreshInterval = setInterval(async () => {
    if (!window.userLat || !window.userLon) return;
    const badge = document.getElementById("rt-nearby-badge");
    if (badge) badge.classList.add("updating");
    try {
      const resp = await fetch(`/api/live-nearby?lat=${window.userLat}&lon=${window.userLon}&type=hospital`);
      const data = await resp.json();
      if (data.results && data.results.length) {
        updateLiveNearby(data.results);
        if (badge) {
          const top = data.results[0];
          badge.textContent = `🏥 ${top.name} · ${top.distance_text}`;
          badge.classList.remove("updating");
        }
      }
    } catch(e) {
      if (badge) badge.classList.remove("updating");
    }
  }, 30000);
}

function updateLiveNearby(results) {
  // If results panel is open, refresh with new data and highlight changed cards
  const list = document.getElementById("results-list");
  if (!list || list.children.length === 0) return;

  // Mark first card as refreshed
  const firstCard = list.firstElementChild;
  if (firstCard) {
    firstCard.classList.add("new-result");
    setTimeout(() => firstCard.classList.remove("new-result"), 1500);
  }
}

// ── UI helpers ─────────────────────────────────────────────────────────────
function setRTStatus(state, label) {
  const dot   = document.getElementById("rt-dot");
  const text  = document.getElementById("rt-status-text");
  if (dot) {
    dot.className = `rt-dot ${state}`;
  }
  if (text) text.textContent = label;
}

function updateRTStats(data) {
  const users = document.getElementById("rt-users");
  const incidents = document.getElementById("rt-incidents");
  if (users) users.textContent = RT.activeUsers || 1;
  if (incidents && data && data.nearby_incidents !== undefined) {
    incidents.textContent = data.nearby_incidents;
  }
}

// ── Incident toast ─────────────────────────────────────────────────────────
function showIncidentToast(data) {
  const inc  = data.incident || {};
  const dist = data.distance_km || "?";
  const icon = {pothole:"🕳",accident:"💥",flooding:"🌊",roadblock:"🚧",breakdown:"🚗",animal:"🐄"}[inc.type] || "⚠";

  const toast = document.createElement("div");
  toast.className = "incident-toast";
  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-body">
      <div class="toast-title">New ${inc.label || inc.type} reported nearby</div>
      <div class="toast-sub">${dist} km away · ${inc.description || "Tap to see on map"}</div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 6000);

  // Also append to chat
  if (window.appendBotMsg) {
    appendBotMsg(`${icon} <b>New incident nearby:</b> ${inc.label || inc.type} reported ${dist}km from you.`);
  }
}

// ── SOS alert ─────────────────────────────────────────────────────────────
function showSOSAlert(data) {
  const toast = document.createElement("div");
  toast.className = "incident-toast";
  toast.style.borderColor = "#E53935";
  toast.style.background = "#2D1515";
  toast.innerHTML = `
    <div class="toast-icon">🆘</div>
    <div class="toast-body">
      <div class="toast-title" style="color:#ff6b6b">SOS Alert nearby!</div>
      <div class="toast-sub">${data.contact || "Someone"} needs help · ${data.message || ""}</div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 10000);
}

// ── Manual refresh button ──────────────────────────────────────────────────
window.manualRefresh = async function() {
  const btn = document.getElementById("rt-refresh-btn");
  if (btn) btn.classList.add("spinning");
  if (window.userLat && window.userLon) {
    sendLocation(window.userLat, window.userLon);
    await new Promise(r => setTimeout(r, 1000));
  }
  if (btn) btn.classList.remove("spinning");
};

// ── Utility ────────────────────────────────────────────────────────────────
function distance(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2-lat1) * Math.PI/180;
  const dLon = (lon2-lon1) * Math.PI/180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

// Auto-init on load
window.addEventListener("load", () => {
  setTimeout(initRealTime, 500); // slight delay to let map init first
});
