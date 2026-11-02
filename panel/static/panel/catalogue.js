/* Categories and Services: drag to reorder, show/hide from the list, and the editor's photo and safety nets. */
(() => {
  const csrf = (document.getElementById("csrf") || document.querySelector("[name=csrfmiddlewaretoken]"))?.value;
  const $ = (s, r = document) => r.querySelector(s);

  /* ---------- list ---------- */
  const page = $("[data-sortlist]"), list = $("#clist");
  if (page && list) {
    const note = $("#order-note");
    const say = (t, bad) => { note.textContent = t; note.style.color = bad ? "var(--bad)" : ""; };
    let dragging = null;
    list.addEventListener("dragstart", (e) => { dragging = e.target.closest(".crow"); if (!dragging) return; e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", dragging.dataset.id); requestAnimationFrame(() => dragging.classList.add("is-dragging")); });
    list.addEventListener("dragover", (e) => {
      if (!dragging) return; e.preventDefault();
      const over = [...list.querySelectorAll(".crow:not(.is-dragging)")].find((r) => e.clientY < r.getBoundingClientRect().top + r.offsetHeight / 2);
      over ? list.insertBefore(dragging, over) : list.appendChild(dragging);
    });
    list.addEventListener("dragend", async () => {
      if (!dragging) return; dragging.classList.remove("is-dragging"); dragging = null;
      const ids = [...list.querySelectorAll(".crow")].map((r) => +r.dataset.id);
      say("Saving the order…");
      try {
        const res = await fetch(page.dataset.order, { method: "POST", body: JSON.stringify({ ids }), headers: { "X-CSRFToken": csrf, "Content-Type": "application/json" }, credentials: "same-origin" });
        if (!res.ok) throw new Error(); say("Order saved.");
      } catch (e) { say("Couldn't save the order. Reload and try again.", true); }
    });
    page.addEventListener("click", async (e) => {
      const b = e.target.closest("[data-toggle-field]"); if (!b || b.disabled) return;
      b.disabled = true;
      try {
        const res = await fetch(page.dataset.toggle.replace("/0/", `/${b.dataset.id}/`), { method: "POST", body: new FormData(), headers: { "X-CSRFToken": csrf }, credentials: "same-origin" });
        const r = await res.json(); if (!res.ok || !r.ok) throw new Error();
        b.classList.toggle("is-on", r.value); b.setAttribute("aria-pressed", r.value);
        b.querySelector("span").textContent = r.value ? "Showing" : "Hidden"; b.closest(".crow").classList.toggle("is-off", !r.value);
      } catch (err) { b.classList.add("is-error"); setTimeout(() => b.classList.remove("is-error"), 1500); }
      b.disabled = false;
    });
  }

  /* ---------- editor ---------- */
  const form = $("form[data-editor]");
  if (!form) return;
  let dirty = false, submitting = false;
  form.addEventListener("input", () => { dirty = true; }); form.addEventListener("change", () => { dirty = true; });
  window.addEventListener("beforeunload", (e) => { if (dirty && !submitting) { e.preventDefault(); e.returnValue = ""; } });
  form.addEventListener("submit", (e) => {
    form.querySelectorAll(".err.js").forEach((x) => x.remove());
    let first = null;
    form.querySelectorAll("[data-required]").forEach((el) => {
      if (el.value.trim()) return;
      el.closest("label").insertAdjacentHTML("beforeend", `<em class="err js">${el.dataset.required}</em>`); first ||= el;
    });
    if (first) { e.preventDefault(); first.focus(); return; }
    submitting = true; $("#save-btn").disabled = true; $("#save-btn").textContent = "Saving…";
  });
  if ($("#main-input")) {
    const frame = $("#main-frame"), input = $("#main-input"), label = $("#main-label"), clear = $("#main-clear"), flag = $("#clear-flag");
    const show = (url) => { frame.innerHTML = url ? `<img id="main-img" src="${url}" alt="">` : '<span class="noimg" id="main-empty">No photo yet</span>'; label.textContent = url ? "Replace photo" : "Add photo"; };
    input.addEventListener("change", () => {
      const f = input.files[0]; if (!f) return;
      if (!f.type.startsWith("image/")) { alert("Please choose a picture (JPG or PNG)."); input.value = ""; return; }
      if (flag) flag.value = ""; show(URL.createObjectURL(f));
    });
    clear?.addEventListener("click", () => { input.value = ""; flag.value = "1"; show(""); clear.hidden = true; dirty = true; });
  }
  const dialog = $("#del-dialog");
  if (dialog) {
    $("#del-open").addEventListener("click", () => dialog.showModal());
    $("#del-cancel").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
    dialog.querySelector("form").addEventListener("submit", () => { submitting = true; });
  }
})();
