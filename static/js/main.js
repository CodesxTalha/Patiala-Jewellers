/* Patiala Jewelers: front-end behaviour. Plain JavaScript, no libraries. */
(() => {
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------- Preloader: holds the page still for a moment, then fades away ---------- */
  const preRoot = document.documentElement;
  const pre = $("#preloader");
  const MIN_SHOW = 2600;                       // lets the lockup finish its entrance before it leaves
  const preStart = performance.now();
  const preActive = preRoot.classList.contains("is-loading") && pre;
  function endPreloader() {
    if (!preActive) return;
    pre.classList.add("is-done");
    setTimeout(() => {
      preRoot.classList.remove("is-loading");
      try { sessionStorage.setItem("pj-intro", "1"); } catch (e) {}
      if (!location.hash) window.scrollTo(0, 0);
      if (window.lenis) window.lenis.start();
    }, 900);
  }
  if (preActive) {
    const done = () => setTimeout(endPreloader, Math.max(0, MIN_SHOW - (performance.now() - preStart)));
    if (document.readyState === "complete") done(); else addEventListener("load", done, { once: true });
  }

  /* ---------- Smooth scrolling (Lenis). Skipped for people who ask for less motion. ---------- */
  let lenis = null;
  if (window.Lenis && !reduceMotion) {
    lenis = new window.Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),   // gentle ease-out
      smoothWheel: true,
    });
    window.lenis = lenis;                                          // map.js pauses it while the map dialog is open
    if (preActive) lenis.stop();                                   // no scrolling while the preloader is up
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
        if (!src) return;
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

  /* ---------- Hero slider: slides or fades, swipe, dots, arrows, autoplay that pauses when you hover or leave the tab ---------- */
  const slider = $("[data-hero-slider]");
  if (slider) {
    const slides = $$(".hero-slide", slider);
    const dots = $$(".hero-dot", slider);
    const phone = matchMedia("(max-width: 899px)");
    const baseSeconds = Math.min(20, Math.max(3, parseInt(slider.dataset.interval, 10) || 6));
    const autoplay = slider.dataset.autoplay === "1" && !reduceMotion && slides.length > 1;
    let current = 0, timer = null, hovering = false, busy = false;

    const loadVideo = (slide) => {
      const v = $("video", slide);
      if (!v) return;
      const src = phone.matches ? (v.dataset.srcMobile || v.dataset.src) : v.dataset.src;
      if (src && v.getAttribute("src") !== src) { v.setAttribute("src", src); v.load(); }
      if (phone.matches && v.dataset.posterMobile) v.poster = v.dataset.posterMobile;
    };
    const play = (slide) => { const v = $("video", slide); if (v) { loadVideo(slide); v.play?.().catch(() => {}); } };
    const pause = (slide) => { const v = $("video", slide); if (v) v.pause?.(); };
    const paint = () => dots.forEach((d, i) => { d.classList.toggle("is-current", i === current); d.setAttribute("aria-selected", i === current ? "true" : "false"); });

    const schedule = () => {
      clearTimeout(timer);
      if (!autoplay || hovering || document.hidden) return;
      const secs = parseInt(slides[current].dataset.seconds, 10) || baseSeconds;
      timer = setTimeout(() => go(current + 1, 1), Math.min(20, Math.max(3, secs)) * 1000);
    };

    function go(n, dir) {
      const next = (n + slides.length) % slides.length;
      if (next === current || busy || slides.length < 2) return;
      busy = true;
      const from = slides[current], to = slides[next];
      dir = dir || (next > current ? 1 : -1);
      to.classList.add("no-anim");
      to.classList.toggle("is-before", dir < 0);
      void to.offsetWidth;                                // lock the starting side before animating
      to.classList.remove("no-anim");
      loadVideo(to); play(to);
      to.classList.add("is-active");
      from.classList.remove("is-active");
      from.classList.toggle("is-before", dir > 0);
      current = next;
      loadVideo(slides[(current + 1) % slides.length]);   // warm the next video
      paint();
      setTimeout(() => { pause(from); busy = false; }, 950);
      schedule();
    }

    slides[0].classList.add("is-active");
    loadVideo(slides[0]); play(slides[0]);
    if (slides.length > 1) loadVideo(slides[1]);
    paint();
    $(".hero-prev", slider)?.addEventListener("click", () => go(current - 1, -1));
    $(".hero-next", slider)?.addEventListener("click", () => go(current + 1, 1));
    dots.forEach((d, i) => d.addEventListener("click", () => go(i, i > current ? 1 : -1)));
    slider.addEventListener("mouseenter", () => { hovering = true; clearTimeout(timer); });
    slider.addEventListener("mouseleave", () => { hovering = false; schedule(); });
    document.addEventListener("visibilitychange", schedule);
    phone.addEventListener("change", () => { slides.forEach((s) => { const v = $("video", s); if (v) { v.removeAttribute("src"); } }); loadVideo(slides[current]); play(slides[current]); });

    // Swipe on touch screens
    let x0 = null, y0 = null;
    slider.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
    slider.addEventListener("touchend", (e) => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      x0 = null;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.4) go(current + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1);
    }, { passive: true });
    slider.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") go(current + 1, 1); else if (e.key === "ArrowLeft") go(current - 1, -1);
    });
    schedule();
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

  /* ---------- Dropdowns: a themed list in place of the browser's own. The real <select> stays in the form. ---------- */
  $$("select.select, select.field-select").forEach((sel, n) => {
    const wrap = document.createElement("div");
    wrap.className = "cselect" + (sel.classList.contains("field-select") ? " cselect--field" : "");
    sel.parentNode.insertBefore(wrap, sel);
    wrap.appendChild(sel);
    sel.classList.add("cselect-native");
    sel.tabIndex = -1;
    sel.setAttribute("aria-hidden", "true");

    const id = "cs" + n;
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "cselect-btn";
    btn.setAttribute("aria-haspopup", "listbox"); btn.setAttribute("aria-expanded", "false");
    if (sel.getAttribute("aria-label")) btn.setAttribute("aria-label", sel.getAttribute("aria-label"));
    btn.innerHTML = '<span class="cselect-value"></span><svg viewBox="0 0 10 6" width="10" height="6" aria-hidden="true"><path d="m1 1 4 4 4-4"/></svg>';
    const list = document.createElement("ul");
    list.className = "cselect-list"; list.id = id; list.setAttribute("role", "listbox"); list.tabIndex = -1;
    list.setAttribute("data-lenis-prevent", "");
    btn.setAttribute("aria-controls", id);
    const opts = [...sel.options].map((o) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option"); li.dataset.value = o.value; li.textContent = o.textContent;
      list.appendChild(li); return li;
    });
    wrap.append(btn, list);

    const label = btn.querySelector(".cselect-value");
    let active = 0;
    const paint = () => {
      const i = Math.max(0, sel.selectedIndex);
      label.textContent = sel.options[i].textContent;
      opts.forEach((li, k) => li.setAttribute("aria-selected", k === i ? "true" : "false"));
    };
    const mark = (i) => {
      active = Math.min(opts.length - 1, Math.max(0, i));
      opts.forEach((li, k) => li.classList.toggle("is-active", k === active));
      opts[active].scrollIntoView({ block: "nearest" });
    };
    const isOpen = () => wrap.classList.contains("is-open");
    const open = () => { wrap.classList.add("is-open"); btn.setAttribute("aria-expanded", "true"); mark(Math.max(0, sel.selectedIndex)); };
    const close = (focus) => { wrap.classList.remove("is-open"); btn.setAttribute("aria-expanded", "false"); if (focus) btn.focus(); };
    const pick = (i) => {
      const changed = sel.selectedIndex !== i;
      sel.selectedIndex = i; paint(); close(true);
      if (changed) sel.dispatchEvent(new Event("change", { bubbles: true }));
    };

    btn.addEventListener("click", () => (isOpen() ? close() : open()));
    opts.forEach((li, k) => {
      li.addEventListener("click", () => pick(k));
      li.addEventListener("mousemove", () => { if (active !== k) mark(k); });
    });
    btn.addEventListener("keydown", (e) => {
      const keys = ["ArrowDown", "ArrowUp", "Home", "End", "Enter", " ", "Escape", "Tab"];
      if (!keys.includes(e.key)) return;
      if (e.key === "Tab") { close(); return; }
      if (e.key === "Escape") { if (isOpen()) { e.preventDefault(); close(); } return; }
      e.preventDefault();
      if (!isOpen()) { open(); return; }
      if (e.key === "ArrowDown") mark(active + 1);
      else if (e.key === "ArrowUp") mark(active - 1);
      else if (e.key === "Home") mark(0);
      else if (e.key === "End") mark(opts.length - 1);
      else pick(active);
    });
    document.addEventListener("click", (e) => { if (isOpen() && !wrap.contains(e.target)) close(); });
    paint();
  });

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
