/* Home section editor: a Collections link can be built from two choices. */
(() => {
  const form = document.getElementById("sec-form");
  if (!form) return;
  document.getElementById("pick-use")?.addEventListener("click", () => {
    const cat = document.getElementById("pick-cat").value, metal = document.getElementById("pick-metal").value;
    const q = new URLSearchParams(); if (cat) q.set("category", cat); if (metal) q.set("metal", metal);
    document.getElementById("link-input").value = "/collections/" + (q.toString() ? "?" + q : "");
    form.dispatchEvent(new Event("input"));
  });
})();
