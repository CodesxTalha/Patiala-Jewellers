/* Admin panel: the phone sidebar, the account menu, and small conveniences. */
(function () {
  var body = document.body;
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-side-open]")) body.classList.add("side-open");
    else if (e.target.closest("[data-side-close]")) body.classList.remove("side-open");
    document.querySelectorAll("details.menu[open]").forEach(function (d) { if (!d.contains(e.target)) d.removeAttribute("open"); });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { body.classList.remove("side-open"); document.querySelectorAll("details.menu[open]").forEach(function (d) { d.removeAttribute("open"); }); }
    if (e.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) {
      var s = document.querySelector(".top-search input"); if (s) { e.preventDefault(); s.focus(); }
    }
  });
})();
