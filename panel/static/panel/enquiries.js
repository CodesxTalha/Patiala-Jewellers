/* Enquiries list: change a status right in the row. Saves at once and keeps the tab counts in step. */
(() => {
  const table = document.querySelector(".etable"), csrf = document.getElementById("csrf");
  if (!table || !csrf) return;
  table.addEventListener("change", async (e) => {
    const select = e.target.closest("[data-status]");
    if (!select) return;
    const row = select.closest(".erow"), previous = [...select.classList].find((c) => c.startsWith("s-")).slice(2);
    select.classList.remove("is-error"); select.classList.add("is-saving"); select.disabled = true;
    try {
      const res = await fetch(table.dataset.statusUrl.replace("/0/", `/${row.dataset.id}/`), {
        method: "POST", headers: { "X-CSRFToken": csrf.value, "Content-Type": "application/x-www-form-urlencoded" }, body: "status=" + encodeURIComponent(select.value),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error);
      select.className = select.className.replace(/\bs-\w+/, "s-" + data.status);
      let total = 0;
      Object.entries(data.counts).forEach(([key, n]) => { total += n; const c = document.querySelector(`[data-count="${key}"]`); if (c) c.textContent = n; });
      const all = document.querySelector('[data-count=""]'); if (all) all.textContent = total;
      const badge = document.querySelector(".nav-item .badge");
      if (badge) { if (data.counts.new) badge.textContent = data.counts.new; else badge.remove(); }
      const filter = new URLSearchParams(location.search).get("status");
      if (filter && filter !== data.status) row.remove();          // it no longer belongs in this tab
    } catch (err) {
      select.value = previous; select.classList.add("is-error");
    } finally {
      select.classList.remove("is-saving"); select.disabled = false;
    }
  });
})();
