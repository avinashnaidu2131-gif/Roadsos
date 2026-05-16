// RoadSoS — Chat Module v2.0

const SERVICE_ICONS = { hospital: "🏥", police: "🚔", ambulance: "🚑", towing: "🚗", fire: "🚒" };
window.lastResults = [];

const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const msgs = document.getElementById("chat-messages");
const typingDots = document.getElementById("typing-dots");

window.useChip = function (btn) {
  // Get button text, remove leading emoji/symbols, keep the words
  var txt = btn.textContent.trim();
  // Remove leading non-letter characters (emojis, spaces, symbols)
  txt = txt.replace(/^[^a-zA-Z\u0900-\u097F\u0C00-\u0C7F\u0B80-\u0BFF]+/, '').trim();
  if (!txt) txt = btn.textContent.trim(); // fallback: use full text
  input.value = txt;
  sendMessage();
};
window.triggerSOS = () => { input.value = "EMERGENCY help me SOS now"; sendMessage(); };

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keydown", e => { if (e.key === "Enter") sendMessage(); });

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  input.value = ""; input.focus();
  appendMsg(text, "user");
  const spinner = appendSpinner();
  typingDots.classList.remove("hidden");
  try {
    const resp = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, lat: window.userLat || null, lon: window.userLon || null, country: "IN", state: "TG" }),
    });
    const data = await resp.json();
    spinner.remove(); typingDots.classList.add("hidden");
    handleResponse(data);
  } catch (err) {
    spinner.remove(); typingDots.classList.add("hidden");
    appendMsg("⚠ Network error. Please check your connection.", "bot error");
  }
}

function handleResponse(data) {
  // AI preamble
  if (data.ai_preamble) appendMsg(data.ai_preamble, "bot ai");
  appendMsg(data.message, "bot");

  // First aid
  if (data.first_aid && window.showFirstAid) {
    showFirstAid(data.first_aid);
    fa.classList.remove("hidden");
  }

  // SOS banner
  const banner = document.getElementById("sos-banner");
  if (data.urgent_banner) {
    banner.classList.remove("hidden");
    document.getElementById("sos-numbers").innerHTML =
      Object.entries(data.quick_numbers || {})
        .map(([k, v]) => `<span class="sos-num" onclick="window.open('tel:${v}')">${k}: ${v}</span>`).join("");
  } else { banner.classList.add("hidden"); }

  // Quick bar
  if (data.quick_numbers && Object.keys(data.quick_numbers).length) {
    document.getElementById("quick-bar").classList.remove("hidden");
    document.getElementById("quick-numbers").innerHTML =
      Object.entries(data.quick_numbers)
        .map(([k, v]) => `<span class="quick-chip" onclick="window.open('tel:${v}')">${k}: <b>${v}</b></span>`).join("");
  }

  if (data.map_pins && data.map_pins.length) addPins(data.map_pins);
  if (data.results && data.results.length) renderResults(data.results);
  if (data.lang) currentLang = data.lang;
}

// ── Result Cards ──────────────────────────────────────────────────────────
function renderResults(results) {
  window.lastResults = results;
  const panel = document.getElementById("results-panel");
  const list = document.getElementById("results-list");
  panel.classList.remove("hidden");
  document.getElementById("results-title").textContent =
    `${results.length} ${results[0]?.type || "service"}(s) found nearby`;

  list.innerHTML = results.map((r, i) => {
    const phones = (r.phone || "").split(";").map(p => p.trim()).filter(Boolean);
    const address = r.address && r.address !== "Address unavailable" ? r.address : "";
    return `
    <div class="result-card" onclick="openDetail(${i})">
      <div class="result-card-top">
        <div class="result-icon icon-${r.type}">${SERVICE_ICONS[r.type] || "📍"}</div>
        <div style="flex:1;min-width:0">
          <div class="result-name">${esc(r.name)}
            <span class="source-badge source-${r.source || 'live'}">${r.source === 'cache' ? '📦' : '🌐'}</span>
          </div>
          ${address ? `<div class="result-addr">📍 ${esc(address)}</div>` : ""}
          ${phones.length ? `<div class="result-phone-line">📞 ${phones.map(p => `<a href="tel:${p}" onclick="event.stopPropagation()">${p}</a>`).join(" · ")}</div>` : ""}
        </div>
        <div class="result-dist">${r.distance_text}</div>
      </div>
      <div class="result-actions">
        <button class="action-btn nav-btn" onclick="event.stopPropagation();showRoute(${r.lat},${r.lon},'${esc(r.name)}')">🧭 Directions</button>
        <button class="action-btn map-btn-sm" onclick="event.stopPropagation();focusPin(${r.lat},${r.lon})">📌 Map</button>
        ${phones.length ? `<a class="action-btn call-btn" href="tel:${phones[0]}" onclick="event.stopPropagation()">📞 Call</a>` : ""}
      </div>
    </div>`;
  }).join("");
}

// ── Detail Panel ──────────────────────────────────────────────────────────
window.openDetail = async function (i) {
  const r = window.lastResults[i];
  if (!r) return;
  const phones = (r.phone || "").split(";").map(p => p.trim()).filter(Boolean);
  const address = r.address && r.address !== "Address unavailable" ? r.address : "Not available";
  document.getElementById("detail-icon").textContent = SERVICE_ICONS[r.type] || "📍";
  document.getElementById("detail-name").textContent = r.name;
  document.getElementById("detail-dist").textContent = r.distance_text + " away";
  document.getElementById("detail-address").textContent = "📍 " + address;
  document.getElementById("detail-phones").innerHTML = phones.length
    ? phones.map(p => `<a class="detail-phone-btn" href="tel:${p}">📞 ${p}</a>`).join("")
    : `<span style="color:var(--muted)">No phone available</span>`;
  document.getElementById("detail-nav-btn").onclick = () => { closeDetail(); showRoute(r.lat, r.lon, r.name); };
  document.getElementById("detail-map-btn").onclick = () => { closeDetail(); focusPin(r.lat, r.lon); };

  // Bed availability for hospitals
  const bedsSection = document.getElementById("beds-section");
  if (r.type === "hospital") {
    bedsSection.classList.remove("hidden");
    document.getElementById("beds-data").innerHTML = `<div style="font-size:12px;color:var(--muted)">Loading...</div>`;
    try {
      const resp = await fetch(`/api/beds?name=${encodeURIComponent(r.name)}&lat=${r.lat}`);
      const beds = await resp.json();
      document.getElementById("beds-data").innerHTML = renderBeds(beds);
    } catch { document.getElementById("beds-data").innerHTML = ""; }
  } else { bedsSection.classList.add("hidden"); }

  document.getElementById("detail-panel").classList.remove("hidden");
};

function renderBeds(data) {
  if (!data.beds) return "";
  return Object.entries(data.beds).map(([type, info]) => `
    <div class="bed-row">
      <span class="bed-type">${type.charAt(0).toUpperCase() + type.slice(1)}</span>
      <span class="bed-dot">${info.dot}</span>
      <span class="bed-count" style="color:${info.color}">${info.available}/${info.total}</span>
      <span class="bed-label" style="color:${info.color}">${info.label}</span>
    </div>`).join("");
}

window.closeDetail = () => document.getElementById("detail-panel").classList.add("hidden");
window.focusPin = function (lat, lon) {
  if (window.map) {
    window.map.setView([lat, lon], 17);
    window.pinMarkers && window.pinMarkers.forEach(m => {
      const ll = m.getLatLng();
      if (Math.abs(ll.lat - lat) < 0.0001 && Math.abs(ll.lng - lon) < 0.0001) m.openPopup();
    });
  }
};

// ── Dark Mode ─────────────────────────────────────────────────────────────
window.toggleDark = function () {
  const html = document.documentElement;
  const dark = html.getAttribute("data-theme") === "dark";
  html.setAttribute("data-theme", dark ? "light" : "dark");
  document.getElementById("dark-btn").textContent = dark ? "🌙" : "☀️";
  localStorage.setItem("roadsos-theme", dark ? "light" : "dark");
};
// Restore theme
(function () { const t = localStorage.getItem("roadsos-theme"); if (t === "dark") { document.documentElement.setAttribute("data-theme", "dark"); document.addEventListener("DOMContentLoaded", () => { const b = document.getElementById("dark-btn"); if (b) b.textContent = "☀️"; }); } })();

// ── Language ──────────────────────────────────────────────────────────────
window.setLanguage = async function (lang) {
  currentLang = lang;
  try {
    const resp = await fetch(`/api/lang/${lang}`);
    const data = await resp.json();
    if (data.placeholder) document.getElementById("chat-input").placeholder = data.placeholder;
  } catch { }
};

// ── Map Modes ─────────────────────────────────────────────────────────────
let currentMode = "services";
window.setMapMode = async function (mode) {
  currentMode = mode;
  ["services", "heatmap", "reports"].forEach(m => {
    const btn = document.getElementById(`btn-${m}`);
    if (btn) btn.classList.toggle("active", m === mode);
  });
  if (mode === "heatmap") loadHeatmap();
  if (mode === "reports") loadReports();
  if (mode === "services") { clearHeatmap(); clearReportMarkers(); }
};

async function loadHeatmap() {
  if (!window.userLat) return;
  clearHeatmap(); clearReportMarkers();
  try {
    const resp = await fetch(`/api/heatmap?lat=${window.userLat}&lon=${window.userLon}`);
    const data = await resp.json();
    const pts = data.points.map(p => [p.lat, p.lon, p.intensity]);
    window._heatLayer = L.heatLayer(pts, {
      radius: 25, blur: 20, maxZoom: 16,
      gradient: { 0.2: "blue", 0.5: "yellow", 0.8: "orange", 1.0: "red" }
    }).addTo(window.map);
  } catch (e) { console.error("Heatmap error:", e); }
}

window.clearHeatmap = function () {
  if (window._heatLayer) { window._heatLayer.remove(); window._heatLayer = null; }
};

let reportMarkers = [];
async function loadReports() {
  if (!window.userLat) return;
  clearHeatmap(); clearReportMarkers();
  try {
    const resp = await fetch(`/api/reports?lat=${window.userLat}&lon=${window.userLon}`);
    const data = await resp.json();
    data.reports.forEach(r => {
      const icon = L.divIcon({
        className: "", html: `<div style="background:${r.color};color:#fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3)">${r.icon}</div>`,
        iconSize: [28, 28], iconAnchor: [14, 14],
      });
      const m = L.marker([r.lat, r.lon], { icon })
        .addTo(window.map)
        .bindPopup(`<b>${r.icon} ${r.label}</b><br>${r.description || ""}<br><small>${r.age} · 👍 ${r.upvotes}</small><br><button onclick="upvoteReport(${r.id})" style="margin-top:4px;padding:2px 8px;cursor:pointer">👍 Confirm</button>`);
      reportMarkers.push(m);
    });
  } catch (e) { console.error("Reports error:", e); }
}

window.clearReportMarkers = function () {
  reportMarkers.forEach(m => m.remove()); reportMarkers = [];
};

window.upvoteReport = async function (id) {
  await fetch(`/api/reports/${id}/upvote`, { method: "POST" });
  loadReports();
};

// ── Road Report Modal ─────────────────────────────────────────────────────
let selectedReportType = "pothole";
window.openReportModal = () => document.getElementById("report-modal").classList.remove("hidden");
window.closeReportModal = () => document.getElementById("report-modal").classList.add("hidden");
window.selectReportType = function (btn) {
  document.querySelectorAll(".report-type-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  selectedReportType = btn.dataset.type;
};
window.submitReport = async function () {
  if (!window.userLat) { alert("Please enable GPS first."); return; }
  const desc = document.getElementById("report-desc").value;
  try {
    const resp = await fetch("/api/reports", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: window.userLat, lon: window.userLon, type: selectedReportType, description: desc }),
    });
    const data = await resp.json();
    if (data.success) {
      closeReportModal();
      appendMsg(`✅ Road issue reported: ${data.icon} ${data.label}. Thank you for helping other drivers!`, "bot");
      document.getElementById("report-desc").value = "";
    }
  } catch { alert("Failed to submit report."); }
};

// ── SOS Share ─────────────────────────────────────────────────────────────
let currentSosUrl = "";
window.shareSOS = async function () {
  if (!window.userLat) { alert("Enable GPS first."); return; }
  try {
    const resp = await fetch("/api/sos/create", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: window.userLat, lon: window.userLon, message: "I need help - RoadSoS emergency alert" }),
    });
    const data = await resp.json();
    currentSosUrl = data.url;
    document.getElementById("sos-link-input").value = data.url;
    document.getElementById("sos-modal").classList.remove("hidden");
  } catch { alert("Could not generate SOS link."); }
};
window.copySosLink = () => { navigator.clipboard.writeText(currentSosUrl); alert("Link copied!"); };
window.whatsappSos = () => { window.open(`https://wa.me/?text=${encodeURIComponent("🚨 EMERGENCY - I need help! My location: " + currentSosUrl)}`); };

// ── Voice ─────────────────────────────────────────────────────────────────
micBtn.addEventListener("click", () => {
  if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) { alert("Voice input not supported. Try Chrome."); return; }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition, rec = new SR();
  rec.lang = "en-IN"; rec.interimResults = false;
  micBtn.classList.add("recording"); micBtn.textContent = "🔴";
  rec.start();
  rec.onresult = e => { input.value = e.results[0][0].transcript; micBtn.classList.remove("recording"); micBtn.textContent = "🎤"; sendMessage(); };
  rec.onerror = rec.onend = () => { micBtn.classList.remove("recording"); micBtn.textContent = "🎤"; };
});

// ── Helpers ───────────────────────────────────────────────────────────────
function appendMsg(text, classes) {
  const isUser = classes.includes("user"), isError = classes.includes("error"), isAI = classes.includes("ai");
  const div = document.createElement("div");
  div.className = "msg " + (isUser ? "user" : "bot") + (isError ? " error" : "") + (isAI ? " ai-msg" : "");
  div.innerHTML = `<div class="avatar">${isUser ? "U" : "R"}</div><div class="bubble">${text}</div>`;
  msgs.appendChild(div); msgs.scrollTop = msgs.scrollHeight;
  return div;
}
function appendSpinner() {
  const div = document.createElement("div"); div.className = "msg bot";
  div.innerHTML = `<div class="avatar">R</div><div class="bubble" style="padding:10px 14px"><div class="spinner-bubble"><div class="spinner-dot"></div><div class="spinner-dot"></div><div class="spinner-dot"></div></div></div>`;
  msgs.appendChild(div); msgs.scrollTop = msgs.scrollHeight; return div;
}
function esc(str) { return String(str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }