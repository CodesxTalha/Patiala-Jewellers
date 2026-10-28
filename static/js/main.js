/* Patiala Jewelers: front-end behaviour. Plain JavaScript, no libraries. */
(() => {
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------- Smooth scrolling (Lenis). Skipped for people who ask for less motion. ---------- */
  let lenis = null;
  if (window.Lenis && !reduceMotion) {
    lenis = new window.Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),   // gentle ease-out
      smoothWheel: true,
    });
    window.lenis = lenis;                                          // map.js pauses it while the map dialog is open
    const raf = (time) => { lenis.raf(time); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);

    // In-page links (#boutiques and so on) glide to the target, stopping below the fixed header.
    document.addEventListener("click", (e) => {
      const a = e.target.closest('a[href*="#"]');
      if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey) return;
      const url = new URL(a.href, location.href);
      if (!url.hash || url.pathname !== location.pathname) return;
      const target = document.querySelector(url.hash);
      if (!target) return;
      e.preventDefault();
      const offset = -(parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--header-h-small")) + 16);
      lenis.scrollTo(target, { offset });
      history.pushState(null, "", url.hash);
    });
    // Text areas scroll on their own
    document.querySelectorAll("textarea").forEach((t) => t.setAttribute("data-lenis-prevent", ""));
  }

  /* ---------- Header: follows the scroll position, frame by frame ----------
     --p goes from 0 (top of the page) to 1 (140px down). The header height, logo size and the PATIALA JEWELERS
     text are all driven by it in CSS, so nothing is a timed animation: it can never lag behind a fast scroll. */
  const root = document.documentElement;
  const fab = $("[data-whatsapp]");
  const RANGE = 140;
  let lastP = -1;

  const onScroll = () => {
    const y = window.scrollY;
    const p = Math.min(1, Math.max(0, y / RANGE));
    if (p !== lastP) { lastP = p; root.style.setProperty("--p", p.toFixed(4)); }
    if (fab) fab.classList.toggle("is-visible", y > 300);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
  lenis?.on("scroll", onScroll);   // Lenis updates the page in its own frame, so listen to it directly: no one-frame delay

  /* ---------- Full-screen mobile menu: slides in from the right ---------- */
  const toggle = $(".nav-toggle");
  const mobileNav = $("#mobile-nav");
  if (toggle && mobileNav) {
    const setOpen = (open) => {
      mobileNav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      document.body.classList.toggle("menu-open", open);
      if (lenis) open ? lenis.stop() : lenis.start();             // the page behind the menu must not scroll
    };
    toggle.addEventListener("click", () => setOpen(!mobileNav.classList.contains("is-open")));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
    $$("a", mobileNav).forEach((a) => a.addEventListener("click", () => setOpen(false)));
    matchMedia("(min-width: 900px)").addEventListener("change", (e) => { if (e.matches) setOpen(false); });
  }

  /* ---------- Hero video: a portrait cut on phones, the wide film elsewhere ---------- */
  const heroVideo = $("[data-hero-video]");
  if (heroVideo) {
    const phone = matchMedia("(max-width: 899px)");   // same breakpoint as the layout switch in main.css
    const d = heroVideo.dataset;
    let loaded = null;

    const loadHero = () => {
      const mobile = phone.matches;
      if (loaded === mobile) return;
      loaded = mobile;
      heroVideo.poster = mobile ? d.posterMobile : heroVideo.getAttribute("poster");
      if (reduceMotion) return;                         // people who ask for less motion get the still poster only
      heroVideo.innerHTML = "";
      [[mobile ? d.webmMobile : d.webm, "video/webm"], [mobile ? d.mp4Mobile : d.mp4, "video/mp4"]].forEach(([src, type]) => {
        const s = document.createElement("source");
        s.src = src; s.type = type;
        heroVideo.appendChild(s);
      });
      heroVideo.load();
      heroVideo.play?.().catch(() => { /* autoplay blocked: the poster stays */ });
    };
    loadHero();
    phone.addEventListener("change", loadHero);
  }

  /* ---------- Fade in sections as they enter the screen ---------- */
  const reveal = $$("[data-reveal], [data-inview]");
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); } });
    }, { threshold: 0.12 });
    reveal.forEach((el) => io.observe(el));
  } else {
    reveal.forEach((el) => el.classList.add("is-visible"));
  }

  /* ---------- Collections: apply the metal filter on change ---------- */
  $$("[data-autosubmit]").forEach((el) => el.addEventListener("change", () => el.form.submit()));

  /* ---------- Product gallery ---------- */
  const mainImg = $("#pdp-main-img");
  $$(".thumbs .thumb").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!mainImg) return;
      mainImg.src = btn.dataset.src;
      $$(".thumbs .thumb").forEach((b) => b.classList.toggle("is-active", b === btn));
    });
  });

  /* ---------- Favorites (saved in this browser only) ---------- */
  const KEY = "pj-favorites";
  const readFavs = () => {
    try { const v = JSON.parse(localStorage.getItem(KEY) || "[]"); return Array.isArray(v) ? v : []; }
    catch { return []; }
  };
  const writeFavs = (list) => { try { localStorage.setItem(KEY, JSON.stringify(list)); } catch { /* storage blocked */ } };

  const syncFavs = () => {
    const favs = readFavs();
    $$("[data-fav]").forEach((btn) => {
      const on = favs.includes(btn.dataset.fav);
      btn.setAttribute("aria-pressed", String(on));
      const text = $("[data-fav-text]", btn);
      if (text) text.textContent = on ? "Saved to favorites" : "Save to favorites";
      if (!text) btn.setAttribute("aria-label", (on ? "Remove from favorites: " : "Save to favorites: ") + (btn.closest(".product-card")?.querySelector("h3")?.textContent || ""));
    });
    $$("[data-fav-link]").forEach((a) => a.classList.toggle("has-favs", favs.length > 0));
  };

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-fav]");
    if (!btn) return;
    e.preventDefault();
    const slug = btn.dataset.fav;
    const favs = readFavs();
    const next = favs.includes(slug) ? favs.filter((s) => s !== slug) : [...favs, slug];
    writeFavs(next);
    syncFavs();
    renderFavoritesPage();
  });

  /* Favorites page: build the grid from the saved slugs */
  const favGrid = $("[data-fav-grid]");
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function renderFavoritesPage() {
    if (!favGrid) return;
    const pieces = JSON.parse($("#all-pieces").textContent);
    const list = readFavs().map((slug) => pieces.find((p) => p.slug === slug)).filter(Boolean);

    favGrid.innerHTML = list.map((p) => `
      <article class="product-card">
        <a href="${esc(p.path)}" class="product-link">
          <div class="product-img"><img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy"></div>
          <div class="product-info"><span class="label">${esc(p.category)}</span><h3>${esc(p.name)}</h3><p class="price">${esc(p.price)}</p></div>
        </a>
        <button type="button" class="fav-btn" data-fav="${esc(p.slug)}" aria-pressed="true" aria-label="Remove from favorites: ${esc(p.name)}">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5S3.5 15 3.5 8.9A4.4 4.4 0 0 1 12 7.2a4.4 4.4 0 0 1 8.5 1.7C20.5 15 12 20.5 12 20.5Z"/></svg>
        </button>
      </article>`).join("");

    const bar = $("[data-fav-bar]");
    const empty = $("[data-fav-empty]");
    if (bar) bar.hidden = list.length === 0;
    if (empty) empty.hidden = list.length > 0;
    const count = $("[data-fav-count]");
    if (count) count.textContent = `${list.length} saved piece${list.length === 1 ? "" : "s"}`;

    const wa = $("[data-fav-whatsapp]");
    if (wa) {
      const lines = list.map((p, i) => `${i + 1}. ${p.name} (${p.price})\n${p.url}`);
      const text = "Hello, I would like to ask about these pieces:\n\n" + lines.join("\n\n");
      wa.href = `https://wa.me/${wa.dataset.waNumber}?text=${encodeURIComponent(text)}`;
    }
    syncFavs();
  }

  syncFavs();
  renderFavoritesPage();
  window.addEventListener("storage", () => { syncFavs(); renderFavoritesPage(); });

  /* ---------- Flash messages fade out ---------- */
  $$(".flash").forEach((el) => {
    setTimeout(() => { el.style.transition = "opacity .5s"; el.style.opacity = "0"; }, 5000);
    setTimeout(() => el.remove(), 5600);
  });
})();
