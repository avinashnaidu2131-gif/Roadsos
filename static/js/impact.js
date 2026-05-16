// RoadSoS — Impact & Safety Score Module

// ── Safety Score ───────────────────────────────────────────────────────────
window.lastSafetyData = null;

window.showSafetyDetails = function() {
  const widget = document.getElementById("safety-widget");
  if (!widget) return;
  widget.classList.toggle("hidden");
  if (!window.userLat || !window.userLon) return;
  fetchSafetyScore();
};

async function fetchSafetyScore() {
  if (!window.userLat || !window.userLon) return;
  try {
    const resp = await fetch(`/api/safety-score?lat=${window.userLat}&lon=${window.userLon}`);
    const data = await resp.json();
    window.lastSafetyData = data;
    renderSafetyScore(data);
    updateSafetyBadge(data);
    checkCoverageGap(data);
  } catch(e) {
    console.warn("[Safety] fetch error:", e);
  }
}

function renderSafetyScore(data) {
  const score  = data.score || 0;
  const fill   = document.getElementById("gauge-fill");
  const scoreEl= document.getElementById("gauge-score");
  const levelEl= document.getElementById("safety-level-text");
  const factors= document.getElementById("safety-factors");
  const rec    = document.getElementById("safety-recommendation");

  if (!fill) return;

  // Animate gauge arc (total arc length = 173)
  const arcLen = Math.round((score / 100) * 173);
  fill.setAttribute("stroke-dasharray", `${arcLen} 173`);
  fill.setAttribute("stroke", data.color || "#43A047");
  if (scoreEl) scoreEl.textContent = score;
  if (levelEl) { levelEl.textContent = data.level; levelEl.style.color = data.color; }

  if (factors && data.factors) {
    factors.innerHTML = data.factors.map(f => `
      <div class="safety-factor ${f.impact > 0 ? 'positive' : 'negative'}">
        <span>${f.impact > 0 ? "✅" : "⚠"} ${f.name}</span>
        <span class="factor-detail">${f.detail}</span>
        <span class="factor-impact" style="color:${f.impact>0?'#69F0AE':'#ff6b6b'}">${f.impact>0?'+':''}${f.impact}</span>
      </div>`).join("");
  }
  if (rec) rec.textContent = data.recommendation || "";
}

function updateSafetyBadge(data) {
  const badge = document.getElementById("safety-badge");
  const dot   = document.getElementById("safety-dot");
  const label = document.getElementById("safety-label");
  if (!badge) return;
  badge.style.borderColor = data.color;
  if (dot) dot.style.color = data.color;
  if (label) label.textContent = `${data.level} (${data.score})`;
}

function checkCoverageGap(data) {
  if (!data.gaps || data.gaps.length === 0) return;
  const critical = data.gaps.filter(g => g.severity === "critical");
  if (critical.length === 0) return;
  const alert = document.getElementById("coverage-alert");
  const sub   = document.getElementById("coverage-sub");
  if (!alert) return;
  alert.classList.remove("hidden");
  if (sub) sub.textContent = critical.map(g => g.message).join(" · ");
}

// Auto-fetch safety score when GPS available
document.addEventListener("DOMContentLoaded", () => {
  setInterval(() => {
    if (window.userLat && window.userLon) fetchSafetyScore();
  }, 60000); // refresh every minute
});

// Also fetch when GPS first acquired
const origSetUserLoc = window.setUserLocation;
window.addEventListener("load", () => {
  const origLocate = document.getElementById("locate-btn");
  if (origLocate) {
    origLocate.addEventListener("click", () => {
      setTimeout(fetchSafetyScore, 3000);
    });
  }
});

// ── Impact Panel ───────────────────────────────────────────────────────────
window.openImpactPanel = function() {
  const panel = document.getElementById("impact-panel");
  if (!panel) return;
  panel.classList.remove("hidden");
  loadImpactData();
};

window.closeImpactPanel = function() {
  const panel = document.getElementById("impact-panel");
  if (panel) panel.classList.add("hidden");
};

async function loadImpactData() {
  const body = document.getElementById("impact-body");
  if (!body) return;
  body.innerHTML = '<div class="impact-loading">Loading impact data...</div>';
  try {
    const resp = await fetch("/api/impact");
    const data = await resp.json();
    renderImpactDashboard(data);
  } catch(e) {
    body.innerHTML = '<div class="impact-loading">Could not load data.</div>';
  }
}

function renderImpactDashboard(data) {
  const body = document.getElementById("impact-body");
  if (!body) return;
  const successRate = data.success_rate || 0;
  const color = successRate >= 80 ? "#43A047" : successRate >= 60 ? "#FF8F00" : "#E53935";

  body.innerHTML = `
    <div class="impact-grid">
      <div class="impact-stat-card lives">
        <div class="impact-stat-icon">❤️</div>
        <div class="impact-stat-value">${data.lives_impacted || 0}</div>
        <div class="impact-stat-label">Lives Potentially Saved</div>
      </div>
      <div class="impact-stat-card searches">
        <div class="impact-stat-icon">🔍</div>
        <div class="impact-stat-value">${data.total_searches || 0}</div>
        <div class="impact-stat-label">Emergency Searches</div>
      </div>
      <div class="impact-stat-card today">
        <div class="impact-stat-icon">📅</div>
        <div class="impact-stat-value">${data.searches_today || 0}</div>
        <div class="impact-stat-label">Searches Today</div>
      </div>
      <div class="impact-stat-card reports">
        <div class="impact-stat-icon">⚠</div>
        <div class="impact-stat-value">${data.road_reports || 0}</div>
        <div class="impact-stat-label">Road Issues Reported</div>
      </div>
    </div>

    <div class="impact-section">
      <div class="impact-section-title">📈 Success Rate</div>
      <div class="impact-progress-wrap">
        <div class="impact-progress-bar">
          <div class="impact-progress-fill" style="width:${successRate}%;background:${color}"></div>
        </div>
        <span class="impact-progress-pct" style="color:${color}">${successRate}%</span>
      </div>
      <div class="impact-progress-sub">${data.successful || 0} of ${data.total_searches || 0} searches found results</div>
    </div>

    ${data.by_service && data.by_service.length ? `
    <div class="impact-section">
      <div class="impact-section-title">🏥 By Service Type</div>
      ${data.by_service.map(s => `
        <div class="impact-service-row">
          <span class="impact-service-icon">${{hospital:"🏥",police:"🚔",ambulance:"🚑",towing:"🚗",fire:"🚒"}[s.type]||"📍"}</span>
          <span class="impact-service-name">${s.type}</span>
          <span class="impact-service-count">${s.count} searches</span>
          <span class="impact-service-avg">${s.avg_results} avg results</span>
        </div>`).join("")}
    </div>` : ""}

    ${data.top_cities && data.top_cities.length ? `
    <div class="impact-section">
      <div class="impact-section-title">🌍 Most Active Cities</div>
      ${data.top_cities.map((c,i) => `
        <div class="impact-city-row">
          <span class="impact-city-rank">#${i+1}</span>
          <span class="impact-city-name">${c.city}</span>
          <span class="impact-city-count">${c.count} searches</span>
        </div>`).join("")}
    </div>` : ""}

    <div class="impact-mission">
      <div class="impact-mission-title">🎯 Our Mission</div>
      <div class="impact-mission-text">
        RoadSoS bridges the gap between road emergencies and emergency services using AI.
        Every second saved in finding a hospital or calling police can be the difference between life and death.
        Built for India's roads — works offline, supports 4 languages, covers 30+ countries.
      </div>
    </div>
  `;
}
