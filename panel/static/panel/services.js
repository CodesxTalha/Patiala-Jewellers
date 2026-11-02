/* Service editor: "what is included" and "how it works" as simple lists. They are written back as text when you save. */
(() => {
  const data = document.getElementById("service-lists");
  const form = document.querySelector("form[data-editor]");
  if (!data || !form) return;
  const lists = JSON.parse(data.textContent);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icon = (n) => `<svg class="ic"><use href="#i-${n}"/></svg>`;

  /* a list of rows: each row has fields, move up, move down and remove */
  function builder(boxId, addId, rows, makeRow, readRow, blank) {
    const box = document.getElementById(boxId);
    const state = rows.length ? rows.map((r) => ({ ...r })) : [];
    const draw = (focus) => {
      box.innerHTML = state.map((r, i) => `<div class="lrow" data-i="${i}"><span class="lnum">${i + 1}</span><div class="lfields">${makeRow(r)}</div>
        <span class="lbtns"><button type="button" class="lbtn up" data-move="-1" ${i === 0 ? "disabled" : ""} aria-label="Move up" title="Move up">${icon("chev-l")}</button>
        <button type="button" class="lbtn down" data-move="1" ${i === state.length - 1 ? "disabled" : ""} aria-label="Move down" title="Move down">${icon("chev-r")}</button>
        <button type="button" class="lbtn" data-remove aria-label="Remove" title="Remove">×</button></span></div>`).join("");
      if (focus != null) box.querySelector(`.lrow[data-i="${focus}"] input`)?.focus();
    };
    box.addEventListener("input", (e) => { const row = e.target.closest(".lrow"); if (row) state[+row.dataset.i] = readRow(row); });
    box.addEventListener("click", (e) => {
      const row = e.target.closest(".lrow"); if (!row) return;
      const i = +row.dataset.i, mv = e.target.closest("[data-move]");
      if (e.target.closest("[data-remove]")) { state.splice(i, 1); draw(); form.dispatchEvent(new Event("input")); }
      else if (mv) { const j = i + +mv.dataset.move; [state[i], state[j]] = [state[j], state[i]]; draw(j); form.dispatchEvent(new Event("input")); }
    });
    box.addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.matches("input")) { e.preventDefault(); state.push(blank()); draw(state.length - 1); } });
    document.getElementById(addId).addEventListener("click", () => { state.push(blank()); draw(state.length - 1); form.dispatchEvent(new Event("input")); });
    draw();
    return state;
  }

  const items = builder("includes-rows", "includes-add", lists.include_list.map((t) => ({ t })),
    (r) => `<input type="text" value="${esc(r.t)}" placeholder="Hand polish" maxlength="200">`,
    (row) => ({ t: row.querySelector("input").value }), () => ({ t: "" }));
  const steps = builder("steps-rows", "steps-add", lists.step_list,
    (r) => `<input type="text" data-k="title" value="${esc(r.title)}" placeholder="Bring it in" maxlength="80"><input type="text" data-k="text" value="${esc(r.text)}" placeholder="A short sentence about this step" maxlength="200">`,
    (row) => ({ title: row.querySelector('[data-k="title"]').value, text: row.querySelector('[data-k="text"]').value }), () => ({ title: "", text: "" }));

  const clean = (v) => v.replace(/[|\n\r]+/g, " ").trim();
  form.addEventListener("submit", () => {
    document.getElementById("includes-field").value = items.map((r) => clean(r.t)).filter(Boolean).join("\n");
    document.getElementById("process-field").value = steps.filter((r) => clean(r.title) || clean(r.text))
      .map((r) => `${clean(r.title)} | ${clean(r.text)}`).join("\n");
  });
})();
