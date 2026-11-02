/* Home section editor: photos preview before you save, and a Collections link can be built from two choices. */
(() => {
  const form = document.getElementById("sec-form");
  if (!form) return;
  form.querySelectorAll("[data-photo]").forEach((box) => {
    const input = box.querySelector("input[type=file]"), img = box.querySelector(".photo-frame img");
    const label = box.querySelector("[data-label]"), clear = box.querySelector("[data-clear]"), flag = box.querySelector("input[type=hidden]");
    input.addEventListener("change", () => {
      const f = input.files[0]; if (!f) return;
      if (!f.type.startsWith("image/")) { alert("Please choose a picture (JPG or PNG)."); input.value = ""; return; }
      img.src = URL.createObjectURL(f); label.textContent = "Replace photo"; if (flag) flag.value = "";
    });
    clear?.addEventListener("click", () => { input.value = ""; flag.value = "1"; img.src = box.dataset.default; label.textContent = "Add your photo"; clear.hidden = true; form.dispatchEvent(new Event("input")); });
  });
  document.getElementById("pick-use")?.addEventListener("click", () => {
    const cat = document.getElementById("pick-cat").value, metal = document.getElementById("pick-metal").value;
    const q = new URLSearchParams(); if (cat) q.set("category", cat); if (metal) q.set("metal", metal);
    document.getElementById("link-input").value = "/collections/" + (q.toString() ? "?" + q : "");
    form.dispatchEvent(new Event("input"));
  });
})();
