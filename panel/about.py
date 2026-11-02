"""About: one page to edit everything on the About page: its heading, the story, the photo, the promises and the closing line."""
import json

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import strip_tags

from shop.content import DEFAULTS
from shop.context_processors import STORY_IMAGE_FALLBACK
from shop.models import AboutValue, ContentBlock, StoreInfo

TEXTS = ("about_label", "about_button", "about_quote", "about_quote_button")
PHOTOS = (("about_image", "clear_image"), ("about_image_mobile", "clear_image_mobile"))
SHOW = ("show_about_story", "show_about_promises", "show_about_closing")
MAX_PHOTO_MB = 12
MAX_PROMISES = 12


def _texts():
    values = {k: DEFAULTS[k][2] for k in TEXTS}
    values.update(dict(ContentBlock.objects.filter(key__in=TEXTS).values_list("key", "text")))
    return values


def _read_promises(raw):
    """The promise rows the page sent, cleaned. Returns (rows, error)."""
    try:
        rows = json.loads(raw or "[]")
        assert isinstance(rows, list)
    except (ValueError, AssertionError):
        return [], "The promises could not be read. Please reload the page."
    clean = []
    for row in rows[:MAX_PROMISES]:
        title, text = strip_tags(str(row.get("title", ""))).strip()[:80], strip_tags(str(row.get("text", ""))).strip()[:200]
        if not title and not text:
            continue
        if not title:
            return [], "Give each promise a short title."
        pk = row.get("id")
        clean.append({"id": int(pk) if str(pk).isdigit() else None, "title": title, "text": text, "on": bool(row.get("on", True))})
    return clean, None


def editor(request, site):
    if not request.user.has_perm("shop.change_storeinfo"):
        return JsonResponse({"error": "No permission"}, status=403)
    store = StoreInfo.load()
    errors = {}
    promises = [{"id": a.pk, "title": a.title, "text": a.text, "on": a.is_active} for a in AboutValue.objects.all()]
    if request.method == "POST":
        post = request.POST
        heading = strip_tags(post.get("about_heading", "")).strip()[:200]
        if not heading:
            errors["about_heading"] = "Give the page a heading."
        rows, problem = _read_promises(post.get("promises"))
        if problem:
            errors["promises"] = problem
        else:
            promises = rows
        old = {f: getattr(store, f).name for f, _ in PHOTOS}
        for field, clear in PHOTOS:
            f = request.FILES.get(field)
            if f:
                try:
                    if f.size > MAX_PHOTO_MB * 1024 * 1024:
                        raise ValidationError(f"That photo is over {MAX_PHOTO_MB} MB.")
                    forms.ImageField().clean(f)
                    f.seek(0)
                    setattr(store, field, f)
                except ValidationError as e:
                    errors[field] = e.messages[0]
            elif post.get(clear):
                setattr(store, field, "")
        if not errors:
            store.about_heading = heading
            for flag in SHOW:
                setattr(store, flag, flag in post)
            store.about_text = post.get("about_text", "").strip()[:5000]
            store.save()
            for field, _ in PHOTOS:
                if old[field] and getattr(store, field).name != old[field]:
                    default_storage.delete(old[field])
            for key in TEXTS:
                if key in post:
                    group, label, _ = DEFAULTS[key]
                    block, _ = ContentBlock.objects.get_or_create(key=key, defaults={"group": group, "label": label})
                    text = strip_tags(post[key]).strip()[:600]
                    if block.text != text:
                        block.text = text
                        block.save(update_fields=["text"])
            existing = {a.pk: a for a in AboutValue.objects.all()}
            keep = set()
            for position, row in enumerate(promises):
                item = existing.get(row["id"]) or AboutValue()
                item.title, item.text, item.is_active, item.display_order = row["title"], row["text"], row["on"], position
                item.save()
                keep.add(item.pk)
            AboutValue.objects.exclude(pk__in=keep).delete()
            messages.success(request, "About page saved.")
            return redirect("admin:about")
        store = StoreInfo.load()          # a failed save shows what is really saved
    context = dict(site.each_context(request), title="About", store=store, texts=_texts(), errors=errors, promises=promises,
                   heading=post.get("about_heading", store.about_heading) if request.method == "POST" else store.about_heading,
                   story_default=STORY_IMAGE_FALLBACK, max_promises=MAX_PROMISES)
    return render(request, "admin/about.html", context)
