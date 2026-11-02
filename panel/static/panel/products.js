/* Products: quick show/feature switches on the list, and the editor's photos, live preview and safety nets. */
(() => {
  const csrf = (document.getElementById("csrf") || document.querySelector("[name=csrfmiddlewaretoken]"))?.value;
  const $ = (s, r = document) => r.querySelector(s);

  /* ---------- list ---------- */
  const list = $(".products-page");
  if (list) {
    list.addEventListener("click", async (e) => {
      const b = e.target.closest("[data-toggle-field]"); if (!b || b.disabled) return;
      b.disabled = true;
      const body = new FormData(); body.append("field", b.dataset.toggleField);
      try {
        const res = await fetch(list.dataset.toggle.replace("/0/", `/${b.dataset.id}/`), { method: "POST", body, headers: { "X-CSRFToken": csrf }, credentials: "same-origin" });
        const r = await res.json();
        if (!res.ok || !r.ok) throw new Error();
        b.classList.toggle("is-on", r.value); b.setAttribute("aria-pressed", r.value);
        if (b.dataset.toggleField === "is_active") {
          const card = b.closest(".pcard"); card.classList.toggle("is-off", !r.value);
          b.querySelector("span").textContent = r.value ? "Showing" : "Hidden";
          const img = $(".pcard-img", card); $(".tag", img)?.remove();
          if (!r.value) img.insertAdjacentHTML("beforeend", '<em class="tag">Hidden</em>');
        }
      } catch (err) { b.classList.add("is-error"); setTimeout(() => b.classList.remove("is-error"), 1500); }
      b.disabled = false;
    });
    $("[data-autosubmit]")?.addEventListener("change", (e) => e.target.form.submit());
  }

  /* ---------- editor ---------- */
  const form = $("#product-form");
  if (!form) return;
  let dirty = false, submitting = false;
  form.addEventListener("input", () => { dirty = true; });
  form.addEventListener("change", () => { dirty = true; });
  window.addEventListener("beforeunload", (e) => { if (dirty && !submitting) { e.preventDefault(); e.returnValue = ""; } });

  /* required fields are checked here first, so a failed save never throws away the photos you chose */
  const need = (el, msg) => {
    const label = el.closest("label"); label.querySelector(".err.js")?.remove();
    if (el.value.trim()) return true;
    label.insertAdjacentHTML("beforeend", `<em class="err js">${msg}</em>`); return false;
  };
  form.addEventListener("submit", (e) => {
    const okName = need(form.name, "Give the piece a name."), okCat = need(form.category, "Choose a category.");
    if (!okName || !okCat) { e.preventDefault(); (okName ? form.category : form.name).focus(); return; }
    submitting = true; $("#save-btn").disabled = true; $("#save-btn").textContent = "Saving…";
  });

  /* live preview card */
  const pvImg = $("#pv-img"), pvName = $("#pv-name"), pvSub = $("#pv-sub");
  let mainUrl = $("#main-img")?.src || "";
  const money = () => { const n = parseFloat(form.price.value.replace(/[, ]/g, "")); return isNaN(n) ? "Price on request" : "Rs " + Math.round(n).toLocaleString("en-US"); };
  const paint = () => {
    pvName.textContent = form.name.value.trim() || "Name of the piece";
    const cat = form.category.selectedOptions[0]; const c = cat && cat.value ? cat.textContent.replace(/ \(hidden\)$/, "") : "Category";
    pvSub.textContent = `${c} · ${money()}`;
    pvImg.style.backgroundImage = mainUrl ? `url("${mainUrl}")` : "";
  };
  form.addEventListener("input", paint); form.addEventListener("change", paint); paint();

  /* main photo */
  const frame = $("#main-frame"), mainInput = $("#main-input"), label = $("#main-label"), clear = $("#main-clear"), flag = $("#clear-flag");
  const showMain = (url) => {
    mainUrl = url; frame.innerHTML = url ? `<img id="main-img" src="${url}" alt="">` : `<span class="noimg" id="main-empty">No photo yet</span>`;
    label.textContent = url ? "Replace photo" : "Add photo"; paint();
  };
  mainInput.addEventListener("change", () => {
    const f = mainInput.files[0]; if (!f) return;
    if (!f.type.startsWith("image/")) { alert("Please choose a picture (JPG or PNG)."); mainInput.value = ""; return; }
    if (flag) flag.value = ""; showMain(URL.createObjectURL(f));
  });
  clear?.addEventListener("click", () => { mainInput.value = ""; flag.value = "1"; showMain(""); clear.hidden = true; dirty = true; });

  /* more photos: existing ones can be marked for removal, new ones are previewed and can be taken back */
  const gal = $("#gal"), galInput = $("#gal-input"), add = $("#gal-add");
  gal.addEventListener("click", (e) => {
    const x = e.target.closest(".gal-x"); if (!x) return;
    const item = x.closest(".gal-item");
    if (item.hasAttribute("data-existing")) {
      const box = $("input[type=checkbox]", item); box.checked = !box.checked; item.classList.toggle("is-removed", box.checked); dirty = true;
    } else { picked.splice(+item.dataset.i, 1); sync(); }
  });
  let picked = [];
  const sync = () => {
    const dt = new DataTransfer(); picked.forEach((f) => dt.items.add(f)); galInput.files = dt.files;
    gal.querySelectorAll(".gal-item[data-new]").forEach((n) => n.remove());
    picked.forEach((f, i) => add.insertAdjacentHTML("beforebegin", `<div class="gal-item" data-new data-i="${i}"><img src="${URL.createObjectURL(f)}" alt=""><button type="button" class="gal-x" aria-label="Don't add this photo" title="Take back">×</button><em class="gal-note is-new">New</em></div>`));
  };
  galInput.addEventListener("change", () => {
    const next = [...galInput.files].filter((f) => f.type.startsWith("image/"));
    picked = picked.concat(next).slice(0, 20); sync(); dirty = true;
  });

  /* delete */
  const dialog = $("#del-dialog");
  if (dialog) {
    $("#del-open").addEventListener("click", () => dialog.showModal());
    $("#del-cancel").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
    dialog.querySelector("form").addEventListener("submit", () => { submitting = true; });
  }
})();
