// RoadSoS Features — safely isolated
(function() {
  'use strict';
  try {

// RoadSoS — Features Module
// Handles: dark mode, language, heatmap, road reports, SOS share, PWA, bed availability

// ── Dark Mode ─────────────────────────────────────────────────────────────
let darkMode = false;
try { darkMode = localStorage.getItem("darkMode") === "1"; } catch (e) { }

function applyDark() {
  document.body.classList.toggle("dark", darkMode);
  const btn = document.getElementById("darkmode-btn");
  if (btn) btn.textContent = darkMode ? "☀️" : "🌙";
}
window.toggleDark = function () {
  darkMode = !darkMode;
  try { localStorage.setItem("darkMode", darkMode ? "1" : "0"); } catch (e) { }
  applyDark();
};

// ── Language ──────────────────────────────────────────────────────────────
let currentLang = "en";
try { currentLang = localStorage.getItem("lang") || "en"; } catch (e) { }
const CHIPS = {
  en: ["🏥 nearest hospital", "🚔 call police", "🚗 car broke down", "🚑 need ambulance now"],
  te: ["🏥 దగ్గరలో ఆసుపత్రి", "🚔 పోలీస్ పిలవండి", "🚗 కారు పాడైంది", "🚑 అంబులెన్స్ పంపండి"],
  hi: ["🏥 नजदीकी अस्पताल", "🚔 पुलिस बुलाएं", "🚗 कार खराब हुई", "🚑 एम्बुलेंस भेजो"],
  ta: ["🏥 அருகில் மருத்துவமனை", "🚔 காவலர் அழையுங்கள்", "🚗 கார் கேடானது", "🚑 ஆம்புலன்ஸ் அனுப்புங்கள்"],
};
const PLACEHOLDERS = {
  en: "Describe your emergency...",
  te: "మీ అత్యవసర స్థితిని వివరించండి...",
  hi: "अपनी आपात स्थिति बताएं...",
  ta: "உங்கள் அவசரநிலையை விவரிக்கவும்...",
};

window.changeLang = function (lang) {
  currentLang = lang;
  localStorage.setItem("lang", lang);
  // Update chips
  const chips = document.getElementById("suggestion-chips");
  if (chips) chips.innerHTML = (CHIPS[lang] || CHIPS.en)
    .map(c => `<button class="chip" onclick="useChip(this)">${c}</button>`).join("");
  // Update placeholder
  const inp = document.getElementById("chat-input");
  if (inp) inp.placeholder = PLACEHOLDERS[lang] || PLACEHOLDERS.en;
  // Fetch and apply UI strings from server
  fetch(`/api/lang/${lang}`).then(r => r.json()).then(strings => {
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (strings[key]) el.textContent = strings[key];
    });
  }).catch(() => { });
};

// Apply on load
document.addEventListener("DOMContentLoaded", () => {
  applyDark();
  const sel = document.getElementById("lang-select");
  if (sel) sel.value = currentLang;
  if (currentLang !== "en") changeLang(currentLang);
});

// ── Map Modes ─────────────────────────────────────────────────────────────
let mapMode = "map";
let heatLayer = null;
let reportMarkers = [];
let pendingReportLat = null, pendingReportLon = null;

window.setMapMode = function (mode) {
  mapMode = mode;
  ["map", "heat", "report", "sos", "injury"].forEach(m => {
    const el = document.getElementById("btn-" + m);
    if (el) el.classList.toggle("active", m === mode);
  });

  const overlay = document.getElementById("report-overlay");
  if (overlay) overlay.classList.toggle("hidden", mode !== "report");

  if (mode === "heatmap") {
    loadHeatmap();
  } else {
    clearHeatmap();
  }

  if (!window.map) return;

  if (mode === "report") {
    window.map.on("click", onMapClickReport); window.map.getCanvas().style.cursor = "crosshair";
    loadReports();
  } else {
    window.map.off("click", onMapClickReport); if(window.map) window.map.getCanvas().style.cursor = "";
    if (overlay) overlay.classList.add("hidden");
  }
};

// ── Heatmap ───────────────────────────────────────────────────────────────
function loadHeatmap() {
  if (!window.userLat) {
    if (window.appendBotMsg) appendBotMsg("📍 Enable GPS first to see the accident heatmap.");
    return;
  }
  fetch(`/api/heatmap?lat=${window.userLat}&lon=${window.userLon}`)
    .then(r => r.json())
    .then(data => {
      clearHeatmap();
      data.points.forEach(p => {
        const radius = 400 + p.intensity * 600;
        const opacity = 0.15 + p.intensity * 0.35;
        const color = p.intensity > 0.7 ? "#E53935" : p.intensity > 0.4 ? "#FF8F00" : "#FDD835";
        const circle = L.circle([p.lat, p.lon], {
          radius, color, fillColor: color, fillOpacity: opacity, weight: 0,
        }).addTo(window.map);
        circle.bindPopup(`<b>⚠ Accident Hotspot</b><br>Risk level: ${Math.round(p.intensity * 100)}%`);
        if (!heatLayer) heatLayer = [];
        heatLayer.push(circle);
      });
    });
}
function clearHeatmap() {
  if (heatLayer) { heatLayer.forEach(l => l.remove()); heatLayer = null; }
}

// ── Road Reports ──────────────────────────────────────────────────────────
const REPORT_TYPES = {
  pothole: { icon: "🕳", label: "Pothole" },
  accident: { icon: "💥", label: "Accident" },
  flooding: { icon: "🌊", label: "Flooding" },
  roadblock: { icon: "🚧", label: "Road Block" },
  breakdown: { icon: "🚗", label: "Breakdown" },
  animal: { icon: "🐄", label: "Animal" },
};

function loadReports() {
  if (!window.userLat) {
    if (window.appendBotMsg) appendBotMsg("📍 Enable GPS first to see road reports.");
    return;
  }
  fetch(`/api/reports?lat=${window.userLat}&lon=${window.userLon}`)
    .then(r => r.json())
    .then(data => {
      reportMarkers.forEach(m => m.remove());
      reportMarkers = [];
      data.reports.forEach(r => {
        const icon = L.divIcon({
          className: "",
          html: `<div style="font-size:22px;filter:drop-shadow(0 2px 3px rgba(0,0,0,0.3))">${r.icon}</div>`,
          iconSize: [28, 28], iconAnchor: [14, 14],
        });
        const m = L.marker([r.lat, r.lon], { icon })
          .addTo(window.map)
          .bindPopup(`<b>${r.icon} ${r.label}</b><br>${r.description || ""}<br>
            <small style="color:#888">${r.age_min < 60 ? r.age_min + "min ago" : Math.round(r.age_min / 60) + "hr ago"} · ${r.dist_km}km away</small><br>
            <button onclick="upvoteReport(${r.id})" style="margin-top:4px;padding:2px 8px;border:none;background:#E3F2FD;border-radius:4px;cursor:pointer">👍 ${r.upvotes}</button>`);
        reportMarkers.push(m);
      });
    });
}

function onMapClickReport(e) {
  pendingReportLat = e.lngLat.lat;
  pendingReportLon = e.lngLat.lng;
  openReportModal();
}

window.openReportModal = function () {
  const grid = document.getElementById("report-type-grid");
  grid.innerHTML = Object.entries(REPORT_TYPES)
    .map(([k, v]) => `<button class="report-type-btn" data-type="${k}" onclick="selectReportType('${k}')">${v.icon}<br><small>${v.label}</small></button>`)
    .join("");
  document.getElementById("report-modal").classList.remove("hidden");
};
window.closeReportModal = function () {
  document.getElementById("report-modal").classList.add("hidden");
};

let selectedReportType = null;
window.selectReportType = function (type) {
  selectedReportType = type;
  document.querySelectorAll(".report-type-btn").forEach(b => {
    b.classList.toggle("selected", b.dataset.type === type);
  });
};

window.submitReport = function () {
  if (!selectedReportType) { alert("Please select a report type."); return; }
  if (!pendingReportLat) { alert("Please tap the map first."); return; }
  const desc = document.getElementById("report-desc").value;
  fetch("/api/reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat: pendingReportLat, lon: pendingReportLon, type: selectedReportType, description: desc }),
  }).then(r => r.json()).then(() => {
    closeReportModal();
    loadReports();
    // Show confirmation in chat
    appendBotMsg(`✅ Road issue reported: ${REPORT_TYPES[selectedReportType].icon} ${REPORT_TYPES[selectedReportType].label} near your location. Thank you!`);
  });
};

window.upvoteReport = function (id) {
  fetch(`/api/reports/${id}/upvote`, { method: "POST" })
    .then(() => loadReports());
};

// ── SOS Share ─────────────────────────────────────────────────────────────
window.openSOSShare = function () {
  const modal = document.getElementById("sos-modal");
  const result = document.getElementById("sos-link-result");
  if (modal) modal.classList.remove("hidden");
  if (result) result.classList.add("hidden");
};
window.createSOSLink = function () {
  if (!window.userLat) { alert("Please enable GPS first."); return; }
  const contact = document.getElementById("sos-contact").value;
  const message = document.getElementById("sos-message").value;
  fetch("/api/sos/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat: window.userLat, lon: window.userLon, contact, message }),
  }).then(r => r.json()).then(data => {
    const box = document.getElementById("sos-link-result");
    box.classList.remove("hidden");
    box.innerHTML = `
      <div style="font-size:12px;color:#555;margin-bottom:6px">Share this link with your emergency contacts:</div>
      <div class="sos-link-url">${data.url}</div>
      <button onclick="navigator.clipboard.writeText('${data.url}').then(()=>this.textContent='✅ Copied!')"
              style="margin-top:8px;padding:6px 16px;background:#1565C0;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px">
        📋 Copy Link
      </button>
      <a href="https://wa.me/?text=${encodeURIComponent('🆘 SOS! I need help. My location: ' + data.url)}"
         target="_blank" style="display:inline-block;margin-top:8px;margin-left:8px;padding:6px 14px;background:#25D366;color:#fff;border-radius:6px;font-size:13px;text-decoration:none">
        📱 WhatsApp
      </a>`;
  });
};

// ── Hospital Bed Availability ─────────────────────────────────────────────
window.loadBedAvailability = function (hospitalName, lat) {
  const section = document.getElementById("bed-section");
  const grid = document.getElementById("bed-info");
  section.classList.remove("hidden");
  grid.innerHTML = `<div style="color:#888;font-size:12px">Loading bed data...</div>`;
  fetch(`/api/beds?name=${encodeURIComponent(hospitalName)}&lat=${lat}`)
    .then(r => r.json())
    .then(data => {
      const statusColor = { available: "#2E7D32", limited: "#E65100", full: "#C62828" };
      const statusIcon = { available: "✅", limited: "⚠️", full: "❌" };
      grid.innerHTML = Object.entries(data.beds).map(([type, info]) => `
        <div class="bed-card" style="border-left:3px solid ${statusColor[info.status]}">
          <div class="bed-type">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
          <div class="bed-count" style="color:${statusColor[info.status]}">${info.available}/${info.total}</div>
          <div class="bed-status">${statusIcon[info.status]} ${info.status}</div>
        </div>`).join("") +
        (data.wait_time_min > 0 ? `<div class="bed-wait">⏱ Est. wait: ${data.wait_time_min} min</div>` : "");
    });
};

// ── PWA Service Worker ────────────────────────────────────────────────────
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js").catch(() => { });
}

// ── First Aid Panel ───────────────────────────────────────────────────────
window.showFirstAid = function (advice) {
  if (!advice) return;
  const panel = document.getElementById("firstaid-panel");
  document.getElementById("firstaid-content").innerHTML =
    advice.split(/\n|\.(?=\s)/).filter(s => s.trim()).map(s =>
      `<div class="firstaid-step">• ${s.trim()}</div>`).join("");
  panel.classList.remove("hidden");
};

// ── Helper: append bot message (used by reports) ──────────────────────────
window.appendBotMsg = function (text) {
  const msgs = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = `<div class="avatar">R</div><div class="bubble">${text}</div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
};

// ── Injury Assessment Modal ───────────────────────────────────────────────
window.openInjuryModal = function () {
  document.getElementById("injury-modal").classList.remove("hidden");
  document.getElementById("injury-result").classList.add("hidden");
  document.getElementById("injury-input").value = "";
  document.getElementById("injury-btn-text").textContent = "🩺 Get First Aid Steps";
  document.getElementById("injury-assess-btn").disabled = false;
  document.querySelectorAll(".injury-chip").forEach(c => c.classList.remove("selected"));
};

window.closeInjuryModal = function () {
  document.getElementById("injury-modal").classList.add("hidden");
};

window.selectInjury = function (btn, text) {
  document.querySelectorAll(".injury-chip").forEach(c => c.classList.remove("selected"));
  btn.classList.add("selected");
  document.getElementById("injury-input").value = text;
  document.getElementById("injury-input").focus();
};

window.assessInjury = async function () {
  const symptom = document.getElementById("injury-input").value.trim();
  if (!symptom) {
    document.getElementById("injury-input").focus();
    document.getElementById("injury-input").style.borderColor = "#E53935";
    setTimeout(() => document.getElementById("injury-input").style.borderColor = "", 1000);
    return;
  }

  const btn = document.getElementById("injury-assess-btn");
  const btnText = document.getElementById("injury-btn-text");
  const result = document.getElementById("injury-result");
  btn.disabled = true;
  btnText.innerHTML = '<span class="spin">⏳</span> Assessing...';
  result.classList.add("hidden");

  try {
    const resp = await fetch("/api/first-aid", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symptom, lat: window.userLat, lon: window.userLon }),
    });
    const data = await resp.json();

    // Render steps
    const steps = (data.steps || []).map((s, i) => `
      <div class="injury-step">
        <div class="injury-step-num">${i + 1}</div>
        <div>${s}</div>
      </div>`).join("");

    result.innerHTML = `
      <div class="injury-result-title">🩺 First Aid for: ${esc(symptom)}</div>
      ${steps}
      ${data.call_number ? `<a class="injury-call-btn" href="tel:${data.call_number}">📞 Call ${data.call_number} Now</a>` : ""}
      ${data.warning ? `<div style="font-size:12px;color:#E65100;margin-top:4px">⚠ ${data.warning}</div>` : ""}
    `;
    result.classList.remove("hidden");

    // Also show in chat
    if (window.appendBotMsg) {
      appendBotMsg(`🩺 <b>First Aid — ${esc(symptom)}:</b><br>${(data.steps || []).map((s, i) => `${i + 1}. ${s}`).join('<br>')}`);
    }
  } catch (e) {
    result.innerHTML = `<div class="injury-step"><div>⚠ Could not fetch first aid. Please call 108 immediately.</div></div>`;
    result.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btnText.textContent = "🩺 Get First Aid Steps";
  }
};

function esc(s) {
  return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
// ── Fix: shift map controls up when results panel is open ─────────────────
function syncMapControls() {
  const panel = document.getElementById("results-panel");
  const mapPanel = document.querySelector(".map-panel");
  if (!panel || !mapPanel) return;
  const isVisible = !panel.classList.contains("hidden");
  mapPanel.classList.toggle("results-visible", isVisible);
}

// Observe results panel visibility changes
document.addEventListener("DOMContentLoaded", () => {
  const panel = document.getElementById("results-panel");
  if (!panel) return;
  const observer = new MutationObserver(syncMapControls);
  observer.observe(panel, { attributes: true, attributeFilter: ["class"] });
  syncMapControls();
});

/* ── findNearby — called by manifest shortcuts (?type=hospital etc.)
   Sends a chat message that the backend already understands, so it goes
   through the same intent-parser → Overpass → response pipeline.          */
window.findNearby = async function (serviceType) {
  const labels = {
    hospital:  "nearest hospital",
    police:    "nearest police station",
    ambulance: "need ambulance",
    towing:    "car towing service",
    fire:      "fire station",
  };
  const msg = labels[serviceType] || `nearest ${serviceType}`;
  // Simulate the user typing and sending the query via chat
  const input = document.getElementById("chat-input");
  if (input) {
    input.value = msg;
    // Trigger sendMessage if it exists, else dispatch Enter
    if (typeof sendMessage === "function") { sendMessage(); }
    else { input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true })); }
  }
};


  } catch(e) {
    console.error('[Features] Fatal error:', e);
    // Register stub functions so buttons don't throw ReferenceError
    window.setMapMode    = window.setMapMode    || function(m){ console.warn('setMapMode not ready:', m); };
    window.openSOSShare  = window.openSOSShare  || function(){ console.warn('openSOSShare not ready'); };
    window.openInjuryModal = window.openInjuryModal || function(){ console.warn('openInjuryModal not ready'); };
    window.toggleDark    = window.toggleDark    || function(){};
    window.changeLang    = window.changeLang    || function(){};
  }
})();
