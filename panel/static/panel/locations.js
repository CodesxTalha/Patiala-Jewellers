/* Location editor: click the map or drag the pin to set the coordinates. Typing the numbers moves the pin too. */
(() => {
  const el = document.getElementById("pick-map"), lat = document.getElementById("lat"), lng = document.getElementById("lng");
  const clear = document.getElementById("pin-clear");
  if (!el || !lat || !lng) return;
  const form = lat.form;
  const ISLAMABAD = [73.0479, 33.6844];
  const num = (v) => { const n = parseFloat(String(v).trim()); return isNaN(n) ? null : n; };
  const valid = (a, o) => a !== null && o !== null && Math.abs(a) <= 90 && Math.abs(o) <= 180;
  if (!window.maplibregl) { el.innerHTML = '<p class="hint" style="padding:1rem">The map could not load. You can still type the two numbers below.</p>'; return; }

  const a0 = num(lat.value), o0 = num(lng.value), has = valid(a0, o0);
  const map = new maplibregl.Map({
    container: el, style: el.dataset.style, center: has ? [o0, a0] : ISLAMABAD, zoom: has ? 15 : 10.5,
    minZoom: 3, maxZoom: 18, attributionControl: false, dragRotate: false, pitchWithRotate: false, touchPitch: false,
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-left");
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

  const dot = document.createElement("div"); dot.className = "pick-dot";
  const marker = new maplibregl.Marker({ element: dot, draggable: true, anchor: "center" });
  const show = (o, a) => { marker.setLngLat([o, a]); if (!marker._map) marker.addTo(map); clear.hidden = false; };
  const write = (o, a) => { lat.value = a.toFixed(6); lng.value = o.toFixed(6); form.dispatchEvent(new Event("input")); };
  if (has) show(o0, a0);

  map.on("click", (e) => { show(e.lngLat.lng, e.lngLat.lat); write(e.lngLat.lng, e.lngLat.lat); });
  marker.on("dragend", () => { const p = marker.getLngLat(); write(p.lng, p.lat); });
  const typed = () => {
    const a = num(lat.value), o = num(lng.value);
    if (valid(a, o)) { show(o, a); map.easeTo({ center: [o, a], zoom: Math.max(map.getZoom(), 14) }); }
  };
  lat.addEventListener("change", typed); lng.addEventListener("change", typed);
  clear.addEventListener("click", () => { marker.remove(); lat.value = ""; lng.value = ""; clear.hidden = true; form.dispatchEvent(new Event("input")); });
})();
