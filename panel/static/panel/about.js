/* About editor: the promises as a simple list (title and a short line, show or hide, move, remove). Written back as JSON on save. */
(() => {
  const data = document.getElementById("promises-data"), box = document.getElementById("promise-rows");
  const form = document.querySelector("form[data-editor]"), field = document.getElementById("promises-field"), add = document.getElementById("promise-add");
  if (!data || !box || !form) return;
  const state = JSON.parse(data.textContent).map((r) => ({ ...r }));
  const max = +add.dataset.max;
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icon = (n) => `<svg class="ic"><use href="#i-${n}"/></svg>`;
  const draw = (focus) => {
    box.innerHTML = state.map((r, i) => `<div class="lrow" data-i="${i}"><span class="lnum">${i + 1}</span>
      <div class="lfields"><input type="text" data-k="title" value="${esc(r.title)}" placeholder="Made in Islamabad" maxlength="80"><input type="text" data-k="text" value="${esc(r.text)}" placeholder="A short line about it" maxlength="200"></div>
      <span class="lbtns"><button type="button" class="lbtn${r.on ? " is-on" : ""}" data-eye aria-pressed="${r.on}" aria-label="Show on the website" title="${r.on ? "Showing" : "Hidden"}">${icon("eye")}</button>
      <button type="button" class="lbtn up" data-move="-1" ${i === 0 ? "disabled" : ""} aria-label="Move up" title="Move up">${icon("chev-l")}</button>
      <button type="button" class="lbtn down" data-move="1" ${i === state.length - 1 ? "disabled" : ""} aria-label="Move down" title="Move down">${icon("chev-r")}</button>
      <button type="button" class="lbtn" data-remove aria-label="Remove" title="Remove">×</button></span></div>`).join("");
    if (focus != null) box.querySelector(`.lrow[data-i="${focus}"] input`)?.focus();
    add.disabled = state.length >= max;
  };
  const changed = () => form.dispatchEvent(new Event("input"));
  box.addEventListener("input", (e) => {
    const row = e.target.closest(".lrow"); if (!row) return;
    const r = state[+row.dataset.i]; r.title = row.querySelector('[data-k="title"]').value; r.text = row.querySelector('[data-k="text"]').value;
  });
  box.addEventListener("click", (e) => {
    const row = e.target.closest(".lrow"); if (!row) return;
    const i = +row.dataset.i, mv = e.target.closest("[data-move]");
    if (e.target.closest("[data-remove]")) { state.splice(i, 1); draw(); changed(); }
    else if (e.target.closest("[data-eye]")) { state[i].on = !state[i].on; draw(); changed(); }
    else if (mv) { const j = i + +mv.dataset.move; [state[i], state[j]] = [state[j], state[i]]; draw(j); changed(); }
  });
  box.addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.matches("input")) { e.preventDefault(); if (state.length < max) { state.push({ id: null, title: "", text: "", on: true }); draw(state.length - 1); } } });
  add.addEventListener("click", () => { state.push({ id: null, title: "", text: "", on: true }); draw(state.length - 1); changed(); });
  form.addEventListener("submit", () => { field.value = JSON.stringify(state); });
  draw();
})();
