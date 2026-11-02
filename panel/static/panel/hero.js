/* Hero editor. Pick a slide, change it, watch the preview, press Save. Nothing changes on the site until then. */
(() => {
  const root = document.getElementById("hero-ed");
  if (!root) return;
  const $ = (s, r = root) => r.querySelector(s);
  const csrf = $("#csrf").value;
  let slides = JSON.parse(document.getElementById("hero-slides").textContent);
  let settings = JSON.parse(document.getElementById("hero-settings").textContent);
  let current = slides.length ? slides[0].id : null;
  let device = "desktop";
  const pending = {};            // slide id -> { fields, files, clearPhone }
  const settingsPending = {};
  let orderDirty = false, busy = false;
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const find = (id) => slides.find((s) => s.id === id);
  const icon = (n) => `<svg class="ic"><use href="#i-${n}"/></svg>`;
  const VIDEO = /\.(mp4|webm|mov)$/i;
  const isVideo = (f) => f.type.startsWith("video/") || VIDEO.test(f.name);
  const pend = (id) => (pending[id] ||= { fields: {}, files: {}, clearPhone: false });
  const isDirty = () => orderDirty || Object.keys(pending).length > 0 || Object.keys(settingsPending).length > 0;

  /* ---------- status and save button ---------- */
  const saved = $("#saved"), saveBtn = $("#save-btn");
  const say = (text, bad) => { saved.textContent = text; saved.className = "saved" + (bad ? " is-bad" : ""); };
  function refresh() {
    const dirty = isDirty();
    saveBtn.disabled = !dirty || busy;
    if (dirty && !busy && !saved.classList.contains("is-bad")) say("You have unsaved changes");
    document.querySelectorAll(".film-item").forEach((li) => li.classList.toggle("is-dirty", !!pending[li.dataset.id]));
  }
  const post = async (url, body) => {
    try {
      const res = await fetch(url, { method: "POST", body, headers: { "X-CSRFToken": csrf, ...(typeof body === "string" ? { "Content-Type": "application/json" } : {}) }, credentials: "same-origin" });
      if (!res.ok) throw new Error(res.status === 403 ? "You can't change this." : "Something went wrong.");
      return await res.json();
    } catch (e) { return { ok: false, errors: { _: e.message || "Couldn't reach the server." } }; }
  };
  const clearErrors = () => root.querySelectorAll("[data-err]").forEach((e) => { e.textContent = ""; });
  const showErrors = (errors) => {
    const all = Object.entries(errors || {});
    all.forEach(([k, v]) => root.querySelectorAll(`[data-err="${k}"]`).forEach((el) => { el.textContent = v; }));
    if (all.length) { say("Not saved: " + all[0][1], true); const el = root.querySelector(".err:not(:empty)"); el?.scrollIntoView({ block: "center", behavior: "smooth" }); }
  };

  /* ---------- editing ---------- */
  function change(key, value) {
    const s = find(current); if (!s) return;
    s[key] = value;
    pend(s.id).fields[key] = value ?? "";
    saved.classList.remove("is-bad");
    drawPreview(); hints(); refresh();
    if (key === "name" || key === "is_active") drawStrip();
  }

  /* ---------- filmstrip ---------- */
  const list = $("#slide-list");
  const thumb = (s) => {
    const img = s.kind === "video" ? (s.poster || s.image_mobile || s.image) : s.image;
    if (img) return `<img src="${esc(img)}" alt="">`;
    if (s.kind === "video" && s.video) return `<video src="${esc(s.video)}#t=0.5" muted preload="metadata"></video>`;
    return `<span class="noimg">${icon("slides")}</span>`;
  };
  function drawStrip() {
    if (list.querySelector(".is-dragging")) return;
    list.innerHTML = slides.map((s, i) => `
      <li class="film-item${s.id === current ? " is-current" : ""}${s.is_active ? "" : " is-off"}${pending[s.id] ? " is-dirty" : ""}" draggable="true" data-id="${s.id}">
        <button type="button" class="film-main" data-pick="${s.id}" title="${esc(s.name)}">
          <span class="film-thumb">${thumb(s)}<em class="film-n">${i + 1}</em>${s.kind === "video" ? `<em class="film-kind">Video</em>` : ""}${s.is_active ? "" : `<em class="film-hidden">Hidden</em>`}<i class="film-dot"></i></span>
          <span class="film-name">${esc(s.name)}</span>
        </button>
        <button type="button" class="film-eye${s.is_active ? " is-on" : ""}" data-eye="${s.id}" title="${s.is_active ? "Showing on the site. Click to hide" : "Hidden. Click to show"}" aria-label="${s.is_active ? "Hide" : "Show"} ${esc(s.name)}">${icon("eye")}</button>
      </li>`).join("");
    $("#add-slide").classList.toggle("is-big", !slides.length);
  }
  list.addEventListener("click", (e) => {
    const pick = e.target.closest("[data-pick]"), eye = e.target.closest("[data-eye]");
    if (pick) { current = +pick.dataset.pick; drawStrip(); drawEditor(); }
    if (eye) { const id = +eye.dataset.eye, s = find(id); s.is_active = !s.is_active; pend(id).fields.is_active = s.is_active; drawStrip(); if (id === current) drawEditor(); refresh(); }
  });
  let dragging = null;
  list.addEventListener("dragstart", (e) => { dragging = e.target.closest(".film-item"); if (!dragging) return; e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", dragging.dataset.id); requestAnimationFrame(() => dragging.classList.add("is-dragging")); });
  list.addEventListener("dragover", (e) => {
    if (!dragging) return; e.preventDefault();
    const over = [...list.querySelectorAll(".film-item:not(.is-dragging)")].find((r) => e.clientX < r.getBoundingClientRect().left + r.offsetWidth / 2);
    over ? list.insertBefore(dragging, over) : list.appendChild(dragging);
  });
  list.addEventListener("dragend", () => {
    if (!dragging) return; dragging.classList.remove("is-dragging");
    const ids = [...list.querySelectorAll(".film-item")].map((r) => +r.dataset.id);
    dragging = null; slides = ids.map(find); orderDirty = true; drawStrip(); drawEditor(); refresh();
  });

  /* ---------- adding a slide (uploads right away, because a slide needs a picture to exist) ---------- */
  const addFile = $("#add-file");
  const addMany = async (files) => {
    for (const file of files) {
      if (isVideo(file) && file.size > 40 * 1024 * 1024) { say("That video is over 40 MB. Compress it first.", true); break; }
      const f = new FormData(); f.append("desktop", file);
      say(`Adding ${file.name}…`);
      const r = await post(root.dataset.add, f);
      if (r.ok) { slides.push(r.slide); current = r.slide.id; saved.classList.remove("is-bad"); drawStrip(); drawEditor(); say("Slide added. Fill it in, then save."); }
      else { say("Not added: " + Object.values(r.errors)[0], true); break; }
    }
  };
  addFile.addEventListener("change", () => { addMany([...addFile.files]); addFile.value = ""; });
  const dropOn = (el, fn) => {
    el.addEventListener("dragover", (e) => { if (e.dataTransfer.types.includes("Files")) { e.preventDefault(); el.classList.add("is-over"); } });
    el.addEventListener("dragleave", () => el.classList.remove("is-over"));
    el.addEventListener("drop", (e) => { if (!e.dataTransfer.files.length) return; e.preventDefault(); el.classList.remove("is-over"); fn([...e.dataTransfer.files]); });
  };
  dropOn($("#add-slide"), addMany);

  /* ---------- slider settings ---------- */
  const setRow = (key, label, control) => `<div class="set-row"><span>${label}</span>${control}</div>`;
  function drawSettings() {
    const box = $("#settings"), open = box.open;
    box.innerHTML = `<summary><h2>Slider settings</h2><span>When there is more than one slide</span></summary>
      <div class="set-grid">
        ${setRow("hero_autoplay", "Change slides automatically", `<input type="checkbox" class="sw" data-set="hero_autoplay" ${settings.hero_autoplay ? "checked" : ""}>`)}
        ${setRow("hero_interval", "Seconds per slide", `<input type="number" class="num" min="3" max="20" data-set="hero_interval" value="${settings.hero_interval}">`)}
        ${setRow("hero_transition", "Movement", `<div class="sg" data-setseg="hero_transition"><button type="button" data-v="slide" class="${settings.hero_transition === "slide" ? "is-on" : ""}">Slide</button><button type="button" data-v="fade" class="${settings.hero_transition === "fade" ? "is-on" : ""}">Fade</button></div>`)}
        ${setRow("hero_show_arrows", "Show arrows", `<input type="checkbox" class="sw" data-set="hero_show_arrows" ${settings.hero_show_arrows ? "checked" : ""}>`)}
        ${setRow("hero_show_dots", "Show dots", `<input type="checkbox" class="sw" data-set="hero_show_dots" ${settings.hero_show_dots ? "checked" : ""}>`)}
      </div><p class="err" data-err="hero_interval"></p>`;
    box.open = open;
  }
  const setSetting = (k, v) => { settings[k] = v; settingsPending[k] = v; saved.classList.remove("is-bad"); refresh(); };
  $("#settings").addEventListener("input", (e) => { const k = e.target.dataset.set; if (k) setSetting(k, e.target.type === "checkbox" ? e.target.checked : e.target.value); });
  $("#settings").addEventListener("click", (e) => {
    const b = e.target.closest(".sg button"); if (!b) return;
    b.parentNode.querySelectorAll("button").forEach((x) => x.classList.toggle("is-on", x === b));
    setSetting(b.parentNode.dataset.setseg, b.dataset.v);
  });

  /* ---------- the editor: preview on the left, settings on the right ---------- */
  const main = $("#ed-main");
  const seg = (key, options, value) => `<div class="sg" data-seg="${key}">${options.map(([v, l]) => `<button type="button" data-v="${v}" class="${value === v ? "is-on" : ""}">${l}</button>`).join("")}</div>`;
  const field = (key, label, value, attrs = "") => `<label class="fld"><span>${label}</span><input type="text" data-f="${key}" value="${esc(value)}" ${attrs}><em class="err" data-err="${key}"></em></label>`;

  function drawEditor() {
    const s = find(current);
    if (!s) {
      main.innerHTML = `<div class="card empty-hero"><h2>Add your first slide</h2><p>Drop a picture or a video here, or press “Add slide” above. Until then the site shows its built-in film.</p>
        <label class="btn-primary">${icon("plus")}Choose a file<input type="file" accept="image/*,video/mp4,video/webm,video/quicktime" multiple hidden data-first></label></div>`;
      const first = $("[data-first]"); first.addEventListener("change", () => addMany([...first.files]));
      dropOn($(".empty-hero"), addMany);
      return;
    }
    main.innerHTML = `
      <div class="ed-preview card">
        <div class="pv-bar"><div class="sg" id="device"><button type="button" data-v="desktop" class="${device === "desktop" ? "is-on" : ""}">Computer</button><button type="button" data-v="phone" class="${device === "phone" ? "is-on" : ""}">Phone</button></div></div>
        <div class="stage" id="stage"><div class="pv" id="pv"></div></div>
      </div>
      <div class="ed-panel card">
        <section class="sec">
          <label class="fld"><span>Slide name <small>only you see this</small></span><input type="text" data-f="name" value="${esc(s.name)}" maxlength="100" placeholder="Eid collection"></label>
        </section>
        <section class="sec"><h3>Picture or video</h3><div id="pictures"></div><p class="err" data-err="file"></p></section>
        <section class="sec">
          <div class="sec-head"><h3>Text</h3><input type="checkbox" class="sw" data-f="show_text" ${s.show_text ? "checked" : ""} aria-label="Show text"></div>
          <div class="text-fields${s.show_text ? "" : " is-off"}">
            ${field("heading", "Heading", s.heading, 'maxlength="120" placeholder="Where love meets gold."')}
            ${field("text", "Line under it", s.text, 'maxlength="220" placeholder="One short sentence"')}
          </div>
        </section>
        <section class="sec">
          <h3 id="link-title"></h3>
          <div class="text-fields${s.show_text ? "" : " is-off"}">${field("button_label", "Button words", s.button_label, 'maxlength="40" placeholder="Shop now"')}</div>
          <label class="fld"><span id="link-label">Link</span><input type="text" data-f="link" value="${esc(s.link)}" maxlength="300" placeholder="/collections/ or https://…"><em class="err" data-err="link"></em></label>
          <p class="note" id="link-note" hidden></p>
          <label class="sw-row"><span>Open in a new tab</span><input type="checkbox" class="sw" data-f="open_in_new_tab" ${s.open_in_new_tab ? "checked" : ""}></label>
        </section>
        <section class="sec"><h3>Look</h3>
          <div class="sw-row"><span>Text position</span>${seg("text_align", [["left", "Left"], ["center", "Centre"]], s.text_align)}</div>
          <div class="sw-row"><span>Text colour</span>${seg("text_tone", [["dark", "Dark"], ["light", "Light"]], s.text_tone)}</div>
          <div class="sw-row"><span>Darken picture</span>${seg("tint", [["none", "No"], ["soft", "A bit"], ["medium", "More"]], s.tint)}</div>
        </section>
        <details class="sec more-sec"${s.seconds || s.show_from || s.show_until ? " open" : ""}>
          <summary><h3>Timing</h3><span>Optional</span></summary>
          <label class="sw-row"><span>Seconds on screen</span><input type="number" class="num" min="3" max="20" data-f="seconds" value="${s.seconds ?? ""}" placeholder="${settings.hero_interval}"></label><p class="err" data-err="seconds"></p>
          <label class="sw-row"><span>Show from</span><input type="date" class="date" data-f="show_from" value="${esc(s.show_from)}"></label>
          <label class="sw-row"><span>Show until</span><input type="date" class="date" data-f="show_until" value="${esc(s.show_until)}"></label><p class="err" data-err="show_until"></p>
        </details>
        <section class="sec sec-end"><button type="button" class="btn-delete" data-del>${icon("trash")}Delete this slide</button></section>
      </div>`;
    drawPictures(); drawPreview(); hints();
  }

  /* what is shown, per device */
  const mediaFor = (s, phone) => s.kind === "video"
    ? { video: phone ? s.video_mobile || s.video : s.video, poster: phone ? s.image_mobile || s.poster || s.image : s.poster || s.image }
    : { image: phone ? s.image_mobile || s.image : s.image };

  function drawPreview() {
    const s = find(current), pv = $("#pv"), stage = $("#stage");
    if (!s || !pv) return;
    const phone = device === "phone";
    stage.classList.toggle("is-phone", phone);
    const m = mediaFor(s, phone), key = JSON.stringify(m);
    if (pv.dataset.media !== key || pv.dataset.dev !== device || !$(".pv-text", pv)) {
      pv.dataset.media = key; pv.dataset.dev = device;
      pv.innerHTML = (m.video ? `<video class="pv-media" src="${esc(m.video)}" ${m.poster ? `poster="${esc(m.poster)}"` : ""} muted loop autoplay playsinline></video>`
        : m.image ? `<img class="pv-media" src="${esc(m.image)}" alt="">` : `<div class="pv-media pv-none">No picture yet</div>`) + `<div class="pv-text"></div>`;
    }
    const hasText = s.show_text && (s.heading || s.text || (s.button_label && s.link));
    pv.className = `pv tint-${s.tint} tone-${s.text_tone} align-${phone ? "center" : s.text_align}${hasText && phone ? " has-fade" : ""}${s.show_text ? "" : " no-text"}`;
    $(".pv-text", pv).innerHTML = `${s.heading ? `<h3>${esc(s.heading)}</h3>` : ""}${s.text ? `<p>${esc(s.text)}</p>` : ""}${s.button_label && s.link ? `<span class="pv-btn">${esc(s.button_label)}</span>` : ""}`;
    $(".pv-hint", pv)?.remove();
    if (!hasText && s.link) pv.insertAdjacentHTML("beforeend", `<span class="pv-hint">The whole slide opens ${esc(s.link)}</span>`);
  }

  /* gentle reminders next to the fields, not blocking errors */
  function hints() {
    const s = find(current); if (!s) return;
    $("#link-title").textContent = s.show_text ? "Button and link" : "Link";
    $("#link-label").textContent = s.show_text ? "Where the button goes" : "Where the whole slide goes";
    const note = $("#link-note");
    const missing = s.show_text && s.button_label && !s.link;
    note.hidden = !missing;
    note.textContent = missing ? "Add a link so the button goes somewhere. It won't show on the site without one." : "";
    $$text();
  }
  function $$text() { const s = find(current); main.querySelectorAll(".text-fields").forEach((el) => el.classList.toggle("is-off", !s.show_text)); }

  function drawPictures() {
    const s = find(current), box = $("#pictures");
    if (!s || !box) return;
    const d = mediaFor(s, false), p = mediaFor(s, true);
    const hasPhone = !!(s.image_mobile || s.video_mobile);
    const tile = (m) => m.video ? `<video src="${esc(m.video)}#t=0.5" muted preload="metadata"></video>` : m.image ? `<img src="${esc(m.image)}" alt="">` : "";
    const accept = "image/*,video/mp4,video/webm,video/quicktime";
    box.innerHTML = `
      <div class="media-row" data-drop="desktop"><span class="mthumb">${tile(d)}</span>
        <span class="mtext"><b>Computer</b><small>${s.kind === "video" ? "Video" : "Wide picture"}</small></span>
        <label class="btn-soft">${icon("upload")}Replace<input type="file" accept="${accept}" data-up="desktop" hidden></label></div>
      <div class="media-row" data-drop="phone"><span class="mthumb tall">${hasPhone ? tile(p) : `<i>Same</i>`}</span>
        <span class="mtext"><b>Phone</b><small>${hasPhone ? "Tall, fills the screen" : "Uses the computer one"}</small></span>
        <span class="mbtns"><label class="btn-soft">${icon("upload")}${hasPhone ? "Replace" : "Add"}<input type="file" accept="image/*${s.kind === "video" ? ",video/mp4,video/webm,video/quicktime" : ""}" data-up="phone" hidden></label>
        ${hasPhone ? `<button type="button" class="btn-soft" data-clear-phone>Remove</button>` : ""}</span></div>
      <p class="hint">A phone picture of about 1080 × 1920 looks best. Videos: MP4, under 40 MB.</p>`;
    box.querySelectorAll("[data-drop]").forEach((el) => dropOn(el, (files) => chooseFile(el.dataset.drop, files[0])));
  }

  /* a chosen file waits in the browser until Save */
  function chooseFile(slot, file) {
    const s = find(current); if (!s || !file) return;
    const video = isVideo(file);
    $('[data-err="file"]').textContent = "";
    if (video && file.size > 40 * 1024 * 1024) { $('[data-err="file"]').textContent = "That video is over 40 MB. Compress it first."; return; }
    if (!video && !file.type.startsWith("image/")) { $('[data-err="file"]').textContent = "Choose a picture or an MP4 video."; return; }
    const p = pend(s.id), url = URL.createObjectURL(file);
    if (slot === "desktop") {
      if (video) { s.kind = "video"; s.video = url; }
      else { s.kind = "image"; s.image = url; s.video = ""; s.video_mobile = ""; s.poster = ""; }
      p.files.desktop = file;
    } else {
      if (video && s.kind !== "video") { $('[data-err="file"]').textContent = "A phone video needs a video on computer too. Use a phone picture instead."; return; }
      if (video) s.video_mobile = url; else s.image_mobile = url;
      p.files.phone = file; p.clearPhone = false;
    }
    saved.classList.remove("is-bad"); drawPictures(); drawPreview(); drawStrip(); refresh();
  }

  /* ---------- editor events ---------- */
  main.addEventListener("input", (e) => {
    const t = e.target, k = t.dataset.f; if (!k) return;
    change(k, t.type === "checkbox" ? t.checked : k === "seconds" ? t.value.trim() : t.value);
  });
  main.addEventListener("change", (e) => {
    const t = e.target;
    if (t.dataset.up && t.files[0]) { chooseFile(t.dataset.up, t.files[0]); t.value = ""; }
  });
  main.addEventListener("click", (e) => {
    const t = e.target, segBtn = t.closest(".sg button");
    if (segBtn) {
      const g = segBtn.parentNode;
      g.querySelectorAll("button").forEach((b) => b.classList.toggle("is-on", b === segBtn));
      if (g.id === "device") { device = segBtn.dataset.v; drawPreview(); }
      else if (g.dataset.seg) change(g.dataset.seg, segBtn.dataset.v);
      return;
    }
    if (t.closest("[data-clear-phone]")) {
      const s = find(current), p = pend(s.id);
      s.image_mobile = ""; s.video_mobile = ""; delete p.files.phone; p.clearPhone = true;
      drawPictures(); drawPreview(); drawStrip(); refresh(); return;
    }
    if (t.closest("[data-del]")) { const s = find(current); $("#del-text").textContent = `“${s.name}” will be removed from the home page. This can't be undone.`; $("#del-dialog").showModal(); }
  });
  const dialog = $("#del-dialog") || document.getElementById("del-dialog");
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  dialog.addEventListener("close", async () => {
    if (dialog.returnValue !== "delete") return;
    const id = current;
    const r = await post(root.dataset.delete.replace("/0/", `/${id}/`), new FormData());
    if (!r.ok) { say("Couldn't delete. Try again.", true); return; }
    const i = slides.indexOf(find(id)); slides = slides.filter((x) => x.id !== id); delete pending[id];
    current = slides.length ? slides[Math.min(i, slides.length - 1)].id : null;
    drawStrip(); drawEditor(); refresh(); say("Slide deleted");
  });

  /* ---------- Save ---------- */
  const flat = (v) => (typeof v === "boolean" ? (v ? "1" : "") : v);
  async function saveAll() {
    if (busy || !isDirty()) return;
    clearErrors(); saved.classList.remove("is-bad");
    // tell the user what is missing before sending anything, so no editing is lost
    for (const id of Object.keys(pending).map(Number)) {
      const s = find(id);
      if (s && s.show_text && s.button_label && !s.link) {
        current = id; drawStrip(); drawEditor();
        showErrors({ link: "Add where the button goes, or clear the button words." });
        return;
      }
    }
    busy = true; saveBtn.disabled = true; say("Saving…");
    let failed = false;
    for (const id of Object.keys(pending).map(Number)) {
      const s = find(id), p = pending[id];
      const f = new FormData();
      Object.entries(p.fields).forEach(([k, v]) => f.append(k, flat(v)));
      if (p.files.desktop) f.append("desktop", p.files.desktop);
      if (p.files.phone) f.append("phone", p.files.phone);
      if (p.clearPhone) f.append("clear_phone", "1");
      const r = await post(root.dataset.save.replace("/0/", `/${id}/`), f);
      if (r.ok) { if (s) Object.assign(s, r.slide); delete pending[id]; }
      else { current = id; failed = true; busy = false; drawStrip(); drawEditor(); showErrors(r.errors); break; }
    }
    if (!failed && Object.keys(settingsPending).length) {
      const f = new FormData(); Object.entries(settingsPending).forEach(([k, v]) => f.append(k, flat(v)));
      const r = await post(root.dataset.settingsUrl, f);
      if (r.ok) { settings = r.settings; Object.keys(settingsPending).forEach((k) => delete settingsPending[k]); }
      else { failed = true; $("#settings").open = true; showErrors(r.errors); }
    }
    if (!failed && orderDirty) {
      const r = await post(root.dataset.order, JSON.stringify({ ids: slides.map((s) => s.id) }));
      if (r.ok) orderDirty = false; else { failed = true; say("Couldn't save the order. Try again.", true); }
    }
    busy = false;
    if (!failed) { drawStrip(); drawEditor(); drawSettings(); say("Saved. Your changes are on the site."); }
    refresh();
  }
  saveBtn.addEventListener("click", saveAll);
  document.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); saveAll(); } });
  window.addEventListener("beforeunload", (e) => { if (isDirty()) { e.preventDefault(); e.returnValue = ""; } });

  drawStrip(); drawSettings(); drawEditor(); refresh();
})();
