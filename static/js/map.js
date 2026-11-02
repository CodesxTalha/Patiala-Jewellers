/* Boutique maps (Contact page, and the home page when there is one location).
   A small map under each boutique, plus one larger map in a dialog when you press "enlarge".
   MapLibre GL with the site's own colour style (static/map/style.json) on free OpenFreeMap tiles. No API key. */
(() => {
  const section = document.getElementById("boutiques");
  const data = document.getElementById("branch-points");
  if (!section || !data || !window.maplibregl) return;

  const style = section.dataset.mapStyle;
  const points = JSON.parse(data.textContent);
  const byId = Object.fromEntries(points.map((p) => [p.id, p]));
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Marker: a simple dot. Soft Black centre, Soft White ring, and a faint gold halo around it.
  const pinEl = (name) => {
    const el = document.createElement("div");
    el.className = "map-pin";
    el.innerHTML = '<span class="pin-halo"></span><span class="pin-dot"></span><span class="pin-label"></span>';
    el.querySelector(".pin-label").textContent = name;
    return el;
  };
  const attribution = () => new maplibregl.AttributionControl({ compact: false });

  /* ----- Small maps: not interactive (so the page scrolls normally), created when they come into view ----- */
  const makeMini = (el) => {
    const p = byId[el.dataset.miniMap];
    if (!p || el.dataset.ready) return;
    el.dataset.ready = "1";
    const map = new maplibregl.Map({
      container: el, style, center: [p.lng, p.lat], zoom: 14.5,
      interactive: false, attributionControl: false, fadeDuration: 0,
    });
    map.addControl(attribution(), "bottom-left");
    new maplibregl.Marker({ element: pinEl(p.name), anchor: "center" }).setLngLat([p.lng, p.lat]).addTo(map);
  };

  const minis = [...section.querySelectorAll("[data-mini-map]")];
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { makeMini(e.target); io.unobserve(e.target); } });
    }, { rootMargin: "300px" });
    minis.forEach((m) => io.observe(m));
  } else {
    minis.forEach(makeMini);
  }

  /* ----- One location: a full-width map you can move around (Ctrl or two fingers to zoom, so the page still scrolls) ----- */
  const makeFull = (el) => {
    const p = byId[el.dataset.fullMap];
    if (!p || el.dataset.ready) return;
    el.dataset.ready = "1";
    const map = new maplibregl.Map({
      container: el, style, center: [p.lng, p.lat], zoom: 15.5, minZoom: 9, maxZoom: 18, attributionControl: false,
      cooperativeGestures: true, dragRotate: false, pitchWithRotate: false, touchPitch: false,
    });
    map.touchZoomRotate.disableRotation();
    map.addControl(attribution(), "bottom-left");
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    new maplibregl.Marker({ element: pinEl(p.name), anchor: "center" }).setLngLat([p.lng, p.lat]).addTo(map);
  };
  section.querySelectorAll("[data-full-map]").forEach((el) => {
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) { makeFull(el); io.disconnect(); } }), { rootMargin: "300px" });
      io.observe(el);
    } else makeFull(el);
  });

  /* ----- Large map in a dialog: one shared map, moved to whichever boutique was chosen ----- */
  const dialog = document.getElementById("map-dialog");
  if (!dialog) return;
  const bigEl = document.getElementById("big-map");
  let big = null;
  let bigMarker = null;

  const openMap = (id) => {
    const p = byId[id];
    if (!p) return;
    dialog.querySelector("[data-md-name]").textContent = p.name;
    dialog.querySelector("[data-md-address]").textContent = p.address || "";
    dialog.showModal();
    document.body.classList.add("modal-open");
    window.lenis?.stop();

    requestAnimationFrame(() => {
      if (!big) {
        big = new maplibregl.Map({
          container: bigEl, style, center: [p.lng, p.lat], zoom: 15.5,
          minZoom: 9, maxZoom: 18, attributionControl: false,
          dragRotate: false, pitchWithRotate: false, touchPitch: false,
        });
        big.touchZoomRotate.disableRotation();
        big.addControl(attribution(), "bottom-left");
        bigMarker = new maplibregl.Marker({ element: pinEl(p.name), anchor: "center" }).setLngLat([p.lng, p.lat]).addTo(big);
      } else {
        bigEl.querySelector(".pin-label").textContent = p.name;
        bigMarker.setLngLat([p.lng, p.lat]);
        big.resize();
        big.jumpTo({ center: [p.lng, p.lat], zoom: 15.5 });
      }
    });
  };

  section.querySelectorAll("[data-open-map]").forEach((el) => {
    el.addEventListener("click", (e) => {
      // The wrapper and the button both carry the attribute; only react once.
      if (el.tagName !== "BUTTON" && e.target.closest("button")) return;
      openMap(Number(el.dataset.openMap));
    });
  });

  dialog.querySelector("[data-md-close]").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });   // click on the dark backdrop
  dialog.addEventListener("close", () => { document.body.classList.remove("modal-open"); window.lenis?.start(); });

  dialog.querySelectorAll("[data-zoom]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!big) return;
      btn.dataset.zoom === "in" ? big.zoomIn({ animate: !reduceMotion }) : big.zoomOut({ animate: !reduceMotion });
    });
  });
})();
