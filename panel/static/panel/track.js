/* Click counting for the Overview page. First-party: nothing leaves this site. */
(() => {
  const track = (kind, label, target) => {
    const body = JSON.stringify({ kind, label: (label || "").slice(0, 120), target: (target || "").slice(0, 300), path: location.pathname });
    try {
      if (navigator.sendBeacon && navigator.sendBeacon("/t/click/", new Blob([body], { type: "application/json" }))) return;
      fetch("/t/click/", { method: "POST", body, keepalive: true, headers: { "Content-Type": "application/json" } });
    } catch (e) { /* counting must never get in the way */ }
  };
  const SOCIAL = /(instagram|facebook|tiktok|youtube|pinterest|twitter)\.com|(^|\.)x\.com|youtu\.be/;
  document.addEventListener("click", (e) => {
    const fav = e.target.closest("[data-fav]");
    if (fav) { if (fav.getAttribute("aria-pressed") !== "true") track("favorite", fav.dataset.fav, location.pathname); return; }
    const a = e.target.closest("a[href]");
    if (!a) return;
    const href = a.getAttribute("href") || "";
    const text = (a.dataset.label || a.getAttribute("aria-label") || a.textContent || "").trim().replace(/\s+/g, " ");
    if (a.dataset.track) return track(a.dataset.track, text, href);
    if (/^tel:/i.test(href)) return track("call", href.slice(4), href);
    if (/^mailto:/i.test(href)) return track("email", href.slice(7), href);
    let host = "";
    try { host = new URL(a.href, location.href).hostname.replace(/^www\./, ""); } catch (err) { return; }
    if (/(^|\.)wa\.me$|whatsapp\.com$/.test(host)) return track("whatsapp", a.closest(".whatsapp-fab") ? "Floating button" : text, href);
    if (SOCIAL.test(host)) return track("social", host, href);
    if (/openstreetmap|maps\.google|google\.com$/.test(host) && /map/i.test(href)) return track("map", text, href);
  }, true);
})();
