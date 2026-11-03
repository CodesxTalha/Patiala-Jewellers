"""Page text: the top of each page (small label, heading, subheading) and a few messages, for the Collections, Services, Contact and Favorites pages, one card per page, one Save button."""
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import strip_tags

from shop.content import DEFAULTS
from shop.models import ContentBlock

# Only wording a visitor really sees and an owner would change. The hero, the Home sections, About and the WhatsApp button are
# edited in their own pages, and small labels deep inside a page keep their built-in wording.
SHOWN = ("collections_label", "collections_title", "collections_lead", "collections_empty", "product_note",
         "services_label", "services_title", "services_lead",
         "contact_label", "contact_title", "contact_lead", "contact_direct_title", "contact_form_title", "contact_thanks",
         "favorites_label", "favorites_title", "favorites_lead", "favorites_empty")
ORDER = ["Collections", "Services", "Contact", "Favorites"]


def _blocks():
    for key in SHOWN:                                                   # a row that is missing is created, so every line can be edited
        group, label, text = DEFAULTS[key]
        ContentBlock.objects.get_or_create(key=key, defaults={"group": group, "label": label, "text": text})
    rows = ContentBlock.objects.filter(key__in=SHOWN)
    groups = {}
    for b in rows:
        b.group, b.label = DEFAULTS[b.key][:2]
        groups.setdefault(b.group, []).append(b)
    names = [g for g in ORDER if g in groups] + sorted(g for g in groups if g not in ORDER)
    return [{"name": g, "rows": sorted(groups[g], key=lambda b: SHOWN.index(b.key))} for g in names]


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
