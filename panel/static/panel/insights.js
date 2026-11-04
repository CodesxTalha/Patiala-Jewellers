/* Visitors and Clicks: a filter changes as soon as it is picked, and Enter searches. */
document.querySelectorAll("form[data-autosubmit-form]").forEach((form) => {
  form.querySelectorAll("select").forEach((s) => s.addEventListener("change", () => form.submit()));
});
