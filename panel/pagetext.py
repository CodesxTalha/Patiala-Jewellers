"""Page text: every line of wording on the public pages, grouped by page, on one page with one Save button.
The About page's wording is edited in About, and the WhatsApp button's wording in Settings."""
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import strip_tags

from shop.content import DEFAULTS
from shop.models import ContentBlock

ELSEWHERE = ("About", "Everywhere")
ORDER = ["Home", "Collections", "Services", "Contact", "Favorites"]


def _blocks():
    for key, (group, label, text) in DEFAULTS.items():                 # a row that is missing is created, so every line can be edited
        if group not in ELSEWHERE:
            ContentBlock.objects.get_or_create(key=key, defaults={"group": group, "label": label, "text": text})
    rows = ContentBlock.objects.exclude(group__in=ELSEWHERE).filter(key__in=DEFAULTS)
    groups = {}
    for b in rows:
        b.group, b.label = DEFAULTS[b.key][:2]                          # the page and wording come from the list, so a moved line follows it
        if b.group not in ELSEWHERE:
            groups.setdefault(b.group, []).append(b)
    names = [g for g in ORDER if g in groups] + sorted(g for g in groups if g not in ORDER)
    return [{"name": g, "rows": sorted(groups[g], key=lambda b: list(DEFAULTS).index(b.key))} for g in names]


def editor(request, site):
    if not request.user.has_perm("shop.change_contentblock"):
        return JsonResponse({"error": "No permission"}, status=403)
    groups = _blocks()
    if request.method == "POST":
        for g in groups:
            for b in g["rows"]:
                field = "t_" + b.key
                if field in request.POST:
                    text = strip_tags(request.POST[field]).strip()[:600]
                    if text != b.text:
                        b.text = text
                        b.save(update_fields=["text"])
        messages.success(request, "Page text saved.")
        return redirect("admin:pagetext")
    return render(request, "admin/pagetext.html", dict(site.each_context(request), title="Page text", groups=groups))
