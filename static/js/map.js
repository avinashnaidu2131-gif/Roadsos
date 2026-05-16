// RoadSoS — Mapbox GL JS Map Module v2.0
// Free public token (works for dev/demo — replace with your own for production)
// Get free token at: https://account.mapbox.com/

const MAPBOX_TOKEN = "pk.eyJ1IjoiYXNodXh5eiIsImEiOiJjbW96YzZwMGYwa3RxMnRzam9lYzhoMG1oIn0.g80o_sOReUwnhxuqsO9waw";

const ICON_CFG = {
  hospital: { letter: "H", bg: "#E53935", shadow: "rgba(229,57,53,0.5)" },
  police: { letter: "P", bg: "#1565C0", shadow: "rgba(21,101,192,0.5)" },
  ambulance: { letter: "A", bg: "#E65100", shadow: "rgba(230,81,0,0.5)" },
  towing: { letter: "T", bg: "#2E7D32", shadow: "rgba(46,125,50,0.5)" },
  fire: { letter: "F", bg: "#BF360C", shadow: "rgba(191,54,12,0.5)" },
  user: { letter: "⦿", bg: "#1565C0", shadow: "rgba(21,101,192,0.6)" },
};

window.map = null;
window.pinMarkers = [];
let userMarker = null;
let routeLayerId = null;
let currentStyle = "dark";

const MAP_STYLES = {
  dark: "mapbox://styles/mapbox/dark-v11",
  satellite: "mapbox://styles/mapbox/satellite-streets-v12",
  streets: "mapbox://styles/mapbox/streets-v12",
  nav: "mapbox://styles/mapbox/navigation-night-v1",
};

// ── Init Mapbox ────────────────────────────────────────────────────────────
function initMap(lat = 17.385, lon = 78.4867) {
  mapboxgl.accessToken = MAPBOX_TOKEN;

  window.map = new mapboxgl.Map({
    container: "map",
    style: MAP_STYLES.dark,
    center: [lon, lat],
    zoom: 13,
    pitch: 30,
    bearing: 0,
    antialias: true,
  });

  // Controls
  window.map.addControl(new mapboxgl.NavigationControl({ showCompass: true }), "top-right");
  window.map.addControl(new mapboxgl.ScaleControl({ maxWidth: 100 }), "bottom-left");
  window.map.addControl(new mapboxgl.FullscreenControl(), "top-right");

  window.map.on("load", () => {
    add3DBuildings();
    addTerrainIfAvailable();
    addStyleSwitcher();
    console.log("[Map] Mapbox loaded ✅");
  });

  // Atmosphere + sky for satellite mode
  window.map.on("style.load", () => {
    if (currentStyle === "satellite") {
      window.map.setFog({
        range: [0.5, 10],
        color: "white",
        "horizon-blend": 0.05,
        "high-color": "#245bde",
        "space-color": "#000000",
        "star-intensity": 0.15,
      });
    }
    add3DBuildings();
  });
}

// ── 3D Buildings ───────────────────────────────────────────────────────────
function add3DBuildings() {
  if (!window.map || !window.map.getStyle()) return;
  if (window.map.getLayer("3d-buildings")) return;
  const layers = window.map.getStyle().layers;
  let labelLayerId;
  for (const layer of layers) {
    if (layer.type === "symbol" && layer.layout["text-field"]) {
      labelLayerId = layer.id; break;
    }
  }
  try {
    window.map.addLayer({
      id: "3d-buildings",
      source: "composite",
      "source-layer": "building",
      filter: ["==", "extrude", "true"],
      type: "fill-extrusion",
      minzoom: 14,
      paint: {
        "fill-extrusion-color": currentStyle === "dark"
          ? ["interpolate", ["linear"], ["get", "height"], [0, "#1a2a3a"], [50, "#243447"], [100, "#2d4059"]]
          : ["interpolate", ["linear"], ["get", "height"], [0, "#aaa"], [50, "#bbb"], [100, "#ccc"]],
        "fill-extrusion-height": ["interpolate", ["linear"], ["zoom"], [14, 0], [14.05, ["get", "height"]]],
        "fill-extrusion-base": ["interpolate", ["linear"], ["zoom"], [14, 0], [14.05, ["get", "min_height"]]],
        "fill-extrusion-opacity": 0.85,
      },
    }, labelLayerId);
  } catch (e) { }
}

function addTerrainIfAvailable() {
  try {
    if (!window.map.getSource("mapbox-dem")) {
      window.map.addSource("mapbox-dem", {
        type: "raster-dem", url: "mapbox://mapbox.mapbox-terrain-dem-v1",
        tileSize: 512, maxzoom: 14,
      });
    }
    window.map.setTerrain({ source: "mapbox-dem", exaggeration: 1.2 });
    window.map.addLayer({
      id: "sky", type: "sky", paint: {
        "sky-type": "atmosphere",
        "sky-atmosphere-sun": [0, 90],
        "sky-atmosphere-sun-intensity": 15,
      }
    });
  } catch (e) { }
}

// ── Style Switcher ─────────────────────────────────────────────────────────
function addStyleSwitcher() {
  // Don't add if already exists
  if (document.getElementById("map-style-switcher")) return;

  const switcher = document.createElement("div");
  switcher.id = "map-style-switcher";
  switcher.className = "map-style-switcher";
  switcher.innerHTML = `
    <button class="style-btn active" data-style="dark" onclick="switchMapStyle('dark',this)">🌙 Dark</button>
    <button class="style-btn" data-style="satellite" onclick="switchMapStyle('satellite',this)">🛰 Satellite</button>
    <button class="style-btn" data-style="streets" onclick="switchMapStyle('streets',this)">🗺 Streets</button>
    <button class="style-btn" data-style="nav" onclick="switchMapStyle('nav',this)">🧭 Nav</button>
  `;
  document.querySelector(".map-panel").appendChild(switcher);
}

window.switchMapStyle = function (style, btn) {
  currentStyle = style;
  window.map.setStyle(MAP_STYLES[style]);
  document.querySelectorAll(".style-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  // Pins will be re-added after style loads
  window.map.once("style.load", () => {
    add3DBuildings();
    reAddPins();
  });
};

// ── User Location ──────────────────────────────────────────────────────────
function setUserLocation(lat, lon) {
  if (!window.map) { initMap(lat, lon); return; }

  // Fly smoothly to user location
  window.map.flyTo({
    center: [lon, lat], zoom: 14, pitch: 45,
    bearing: 0, speed: 1.4, curve: 1.4,
    easing: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
  });

  // Remove old user marker
  if (userMarker) userMarker.remove();

  // Create custom user marker
  const el = document.createElement("div");
  el.className = "mapbox-user-marker";
  el.innerHTML = `
    <div class="user-marker-pulse"></div>
    <div class="user-marker-dot"></div>
  `;
  userMarker = new mapboxgl.Marker({ element: el, anchor: "center" })
    .setLngLat([lon, lat])
    .setPopup(new mapboxgl.Popup({ offset: 20, className: "roadsos-popup" })
      .setHTML("<b>📍 You are here</b>"))
    .addTo(window.map);
}

// ── Pins ───────────────────────────────────────────────────────────────────
window.clearPins = function () {
  window.pinMarkers.forEach(m => m.remove());
  window.pinMarkers.length = 0;
  clearRoute();
};

let lastPins = [];

window.addPins = function (pins) {
  clearPins();
  lastPins = pins;
  pins.forEach((pin, i) => {
    const cfg = ICON_CFG[pin.type] || ICON_CFG.hospital;
    const el = document.createElement("div");
    el.className = "mapbox-service-marker";
    el.style.cssText = `
      background:${cfg.bg};width:36px;height:36px;border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;
      border:2.5px solid rgba(255,255,255,0.9);
      box-shadow:0 4px 14px ${cfg.shadow},0 2px 6px rgba(0,0,0,0.4);
      cursor:pointer;transition:transform 0.2s,box-shadow 0.2s;
    `;
    el.innerHTML = `<span style="transform:rotate(45deg);color:#fff;font-weight:800;font-size:13px;font-family:'DM Sans',sans-serif">${cfg.letter}</span>`;
    el.onmouseover = () => { el.style.transform = "rotate(-45deg) scale(1.15)"; el.style.boxShadow = `0 6px 20px ${cfg.shadow}`; };
    el.onmouseout = () => { el.style.transform = "rotate(-45deg) scale(1)"; el.style.boxShadow = `0 4px 14px ${cfg.shadow},0 2px 6px rgba(0,0,0,0.4)`; };

    const popup = new mapboxgl.Popup({ offset: [0, -30], className: "roadsos-popup", closeButton: false })
      .setHTML(`
        <div style="font-family:'DM Sans',sans-serif;padding:2px">
          <b style="font-size:13px">${pin.name}</b>
          <div style="color:#888;font-size:11px;margin-top:2px">${pin.distance_text} away</div>
        </div>`);

    const marker = new mapboxgl.Marker({ element: el, anchor: "bottom" })
      .setLngLat([pin.lon, pin.lat])
      .setPopup(popup)
      .addTo(window.map);

    window.pinMarkers.push(marker);

    // Stagger pin drop animation
    el.style.opacity = "0";
    el.style.transition = "opacity 0.3s, transform 0.2s, box-shadow 0.2s";
    setTimeout(() => { el.style.opacity = "1"; }, i * 80);
  });

  // Fit bounds to show all pins + user
  if (pins.length > 0) {
    const bounds = new mapboxgl.LngLatBounds();
    pins.forEach(p => bounds.extend([p.lon, p.lat]));
    if (userMarker) bounds.extend(userMarker.getLngLat());
    window.map.fitBounds(bounds, { padding: { top: 80, bottom: 220, left: 40, right: 40 }, maxZoom: 16, duration: 1200 });
  }
};

function reAddPins() {
  if (lastPins.length) setTimeout(() => window.addPins(lastPins), 100);
}

// ── In-app Routing via OSRM ────────────────────────────────────────────────
window.showRoute = async function (destLat, destLon, placeName) {
  if (!window.userLat || !window.userLon) {
    alert("Please enable GPS or set your location first."); return;
  }
  clearRoute();
  showRoutePanel("⏳ Calculating route...", placeName, null);
  document.getElementById("results-panel")?.classList.add("hidden");

  try {
    const url = `https://router.project-osrm.org/route/v1/driving/`
      + `${window.userLon},${window.userLat};${destLon},${destLat}`
      + `?overview=full&geometries=geojson&steps=true`;
    const resp = await fetch(url);
    const data = await resp.json();
    if (data.code !== "Ok" || !data.routes.length) {
      showRoutePanel("❌ Route not found.", placeName, null); return;
    }
    const route = data.routes[0];
    const distKm = (route.distance / 1000).toFixed(1);
    const mins = Math.round(route.duration / 60);

    // Remove old route layers
    clearRouteLayer();

    // Add route source + layers to Mapbox
    window.map.addSource("route", { type: "geojson", data: { type: "Feature", geometry: route.geometry } });

    // Glow effect — two layers
    window.map.addLayer({
      id: "route-glow", type: "line", source: "route",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": "#1565C0", "line-width": 12, "line-opacity": 0.2 }
    });
    window.map.addLayer({
      id: "route-line", type: "line", source: "route",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": ["interpolate", ["linear"], ["line-progress"], [0, "#1565C0"], [0.5, "#00BCD4"], [1, "#43A047"]],
        "line-width": 5, "line-opacity": 0.95, "line-gradient": true,
      }
    });

    routeLayerId = "route-line";

    // Animated dash
    let dashOffset = 0;
    const animateDash = () => {
      if (!window.map.getLayer("route-line")) return;
      dashOffset -= 0.5;
      window.map.setPaintProperty("route-line", "line-dasharray", [2, 1]);
      requestAnimationFrame(animateDash);
    };
    animateDash();

    // Fit map to route
    const coords = route.geometry.coordinates;
    const bounds = coords.reduce((b, c) => b.extend(c), new mapboxgl.LngLatBounds(coords[0], coords[0]));
    window.map.fitBounds(bounds, { padding: { top: 80, bottom: 80, left: 60, right: 60 }, duration: 1000 });

    // Build steps
    const steps = route.legs[0].steps
      .filter(s => s.distance > 0)
      .map(s => ({
        icon: getTurnIcon(s.maneuver.type, s.maneuver.modifier),
        dist: s.distance >= 1000 ? `${(s.distance / 1000).toFixed(1)}km` : `${Math.round(s.distance)}m`,
        name: s.name || "",
        instruction: formatStep(s),
      }));

    showRoutePanel(`${distKm} km · ${mins} min`, placeName, steps);

    // Add destination pin
    const destEl = document.createElement("div");
    destEl.innerHTML = `<div style="font-size:28px;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.5))">📍</div>`;
    new mapboxgl.Marker({ element: destEl, anchor: "bottom" })
      .setLngLat([destLon, destLat])
      .addTo(window.map);

  } catch (e) {
    showRoutePanel("❌ Network error fetching route.", placeName, null);
  }
};

function clearRouteLayer() {
  try { if (window.map.getLayer("route-glow")) window.map.removeLayer("route-glow"); } catch (e) { }
  try { if (window.map.getLayer("route-line")) window.map.removeLayer("route-line"); } catch (e) { }
  try { if (window.map.getSource("route")) window.map.removeSource("route"); } catch (e) { }
  routeLayerId = null;
}

window.clearRoute = function () {
  clearRouteLayer();
  document.getElementById("route-panel")?.classList.add("hidden");
};

function showRoutePanel(summary, placeName, steps) {
  const panel = document.getElementById("route-panel");
  if (panel) panel.classList.remove("hidden");
  const titleEl = document.getElementById("route-title");
  const summaryEl = document.getElementById("route-summary");
  if (titleEl) titleEl.textContent = `To: ${placeName}`;
  if (summaryEl) summaryEl.textContent = summary;
  const stepsEl = document.getElementById("route-steps");
  if (!stepsEl) return;
  if (!steps) { stepsEl.innerHTML = ""; return; }
  stepsEl.innerHTML = steps.map((s, i) => `
    <div class="route-step ${i === 0 ? 'first-step' : ''}">
      <div class="step-icon">${s.icon}</div>
      <div class="step-body">
        <div class="step-instruction">${s.instruction}${s.name ? ` on <b>${s.name}</b>` : ""}</div>
        <div class="step-dist">${s.dist}</div>
      </div>
    </div>`).join("");
}

function getTurnIcon(type, mod) {
  if (type === "depart") return "🚦";
  if (type === "arrive") return "🏁";
  if (type === "roundabout") return "🔄";
  if (!mod) return "⬆️";
  if (mod.includes("left")) return mod.includes("sharp") ? "↰" : "⬅️";
  if (mod.includes("right")) return mod.includes("sharp") ? "↱" : "➡️";
  if (mod === "uturn") return "↩️";
  return "⬆️";
}

function formatStep(s) {
  const type = s.maneuver.type || "", mod = s.maneuver.modifier || "";
  if (type === "depart") return "Start";
  if (type === "arrive") return "Arrive";
  if (type === "turn") return `Turn ${mod}`;
  if (type === "continue") return "Continue straight";
  if (type === "roundabout") return "Enter roundabout";
  return type.charAt(0).toUpperCase() + type.slice(1);
}

window.focusPin = function (lat, lon) {
  if (!window.map) return;
  window.map.flyTo({
    center: [lon, lat], zoom: 17, pitch: 60, duration: 1200,
    easing: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
  });
  window.pinMarkers.forEach(m => {
    const ll = m.getLngLat();
    if (Math.abs(ll.lat - lat) < 0.0001 && Math.abs(ll.lng - lon) < 0.0001) m.togglePopup();
  });
};

// ── Locate Me ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const locBtn = document.getElementById("locate-btn");
  if (locBtn) locBtn.addEventListener("click", () => {
    if (!navigator.geolocation) { alert("Geolocation not supported."); return; }
    locBtn.textContent = "⏳ Locating...";
    navigator.geolocation.getCurrentPosition(
      pos => {
        window.userLat = pos.coords.latitude;
        window.userLon = pos.coords.longitude;
        setUserLocation(window.userLat, window.userLon);
        document.getElementById("mode-badge").className = "mode-badge online";
        document.getElementById("mode-badge").textContent = "● LIVE";
        document.getElementById("location-bar")?.classList.add("hidden");
        locBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="7" cy="7" r="2.5"/><line x1="7" y1="1" x2="7" y2="3"/><line x1="7" y1="11" x2="7" y2="13"/><line x1="1" y1="7" x2="3" y2="7"/><line x1="11" y1="7" x2="13" y2="7"/></svg> Locate Me`;
      },
      err => {
        document.getElementById("location-bar")?.classList.remove("hidden");
        document.getElementById("mode-badge").className = "mode-badge offline";
        document.getElementById("mode-badge").textContent = "● GPS OFF";
        locBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="7" cy="7" r="2.5"/><line x1="7" y1="1" x2="7" y2="3"/><line x1="7" y1="11" x2="7" y2="13"/><line x1="1" y1="7" x2="3" y2="7"/><line x1="11" y1="7" x2="13" y2="7"/></svg> Locate Me`;
      }
    );
  });
});

// ── Auto init on load ──────────────────────────────────────────────────────
window.addEventListener("load", () => {
  initMap();
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        window.userLat = pos.coords.latitude;
        window.userLon = pos.coords.longitude;
        setUserLocation(window.userLat, window.userLon);
        document.getElementById("location-bar")?.classList.add("hidden");
      },
      () => {
        document.getElementById("location-bar")?.classList.remove("hidden");
        document.getElementById("mode-badge").className = "mode-badge offline";
        document.getElementById("mode-badge").textContent = "● GPS OFF";
      }
    );
  } else {
    document.getElementById("location-bar")?.classList.remove("hidden");
  }
});

// ── Manual location ────────────────────────────────────────────────────────
window.setManualLocation = function () {
  const val = document.getElementById("location-input")?.value.trim();
  if (!val) return;
  const coord = val.match(/^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$/);
  if (coord) {
    window.userLat = parseFloat(coord[1]);
    window.userLon = parseFloat(coord[2]);
    setUserLocation(window.userLat, window.userLon);
    document.getElementById("location-bar")?.classList.add("hidden");
    return;
  }
  fetch(`/api/geocode?q=${encodeURIComponent(val)}`)
    .then(r => r.json())
    .then(data => {
      if (data.lat) {
        window.userLat = data.lat;
        window.userLon = data.lon;
        setUserLocation(window.userLat, window.userLon);
        document.getElementById("location-bar")?.classList.add("hidden");
      } else {
        alert("Location not found. Try coordinates: 17.38,78.48");
      }
    });
};

// ── Heatmap on Mapbox ─────────────────────────────────────────────────────
window.addMapboxHeatmap = function (points) {
  // Remove existing
  try { if (window.map.getLayer("heatmap-layer")) window.map.removeLayer("heatmap-layer"); } catch (e) { }
  try { if (window.map.getSource("heatmap-data")) window.map.removeSource("heatmap-data"); } catch (e) { }

  const geojson = {
    type: "FeatureCollection",
    features: points.map(p => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [p.lon, p.lat] },
      properties: { weight: p.intensity },
    })),
  };

  window.map.addSource("heatmap-data", { type: "geojson", data: geojson });
  window.map.addLayer({
    id: "heatmap-layer", type: "heatmap", source: "heatmap-data",
    paint: {
      "heatmap-weight": ["interpolate", ["linear"], ["get", "weight"], [0, 0], [1, 1]],
      "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], [0, 1], [12, 3]],
      "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"],
        [0, "rgba(0,0,255,0)"], [0.2, "rgba(0,100,255,0.5)"],
        [0.4, "rgba(0,255,200,0.7)"], [0.6, "rgba(255,200,0,0.85)"],
        [0.8, "rgba(255,100,0,0.9)"], [1, "rgba(229,57,53,1)"],
      ],
      "heatmap-radius": ["interpolate", ["linear"], ["zoom"], [10, 20], [14, 50]],
      "heatmap-opacity": 0.85,
    },
  });
};

window.clearMapboxHeatmap = function () {
  try { if (window.map.getLayer("heatmap-layer")) window.map.removeLayer("heatmap-layer"); } catch (e) { }
  try { if (window.map.getSource("heatmap-data")) window.map.removeSource("heatmap-data"); } catch (e) { }
};
