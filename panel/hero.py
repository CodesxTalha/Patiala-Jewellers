"""The visual hero editor: one page where slides are added, ordered, edited and previewed. Saves as you type."""
import json
import os

from django import forms
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from shop.models import HeroSlide, StoreInfo

MAX_VIDEO_MB = 40
VIDEO_TYPES = ("video/mp4", "video/webm", "video/quicktime")
TEXT = ("name", "heading", "text", "button_label", "link", "text_color", "text_color_mobile", "text_align", "tint")
FLAGS = ("show_text", "open_in_new_tab", "is_active")
DATES = ("show_from", "show_until")
SETTING_FLAGS = ("hero_autoplay", "hero_show_arrows", "hero_show_dots")


def slide_json(s):
    url = lambda f: f.url if f else ""
    return {
        "id": s.pk, "name": s.name, "kind": s.kind, "is_active": s.is_active, "show_text": s.show_text,
        "heading": s.heading, "text": s.text, "button_label": s.button_label, "link": s.link,
        "open_in_new_tab": s.open_in_new_tab, "text_color": s.ink, "text_color_mobile": s.text_color_mobile, "text_align": s.text_align, "tint": s.tint,
        "seconds": s.seconds, "show_from": s.show_from.isoformat() if s.show_from else "",
        "show_until": s.show_until.isoformat() if s.show_until else "",
        "image": url(s.image), "image_mobile": url(s.image_mobile), "video": url(s.video),
        "video_mobile": url(s.video_mobile), "poster": url(s.poster),
    }


def settings_json(info):
    return {"hero_autoplay": info.hero_autoplay, "hero_interval": info.hero_interval,
            "hero_transition": info.hero_transition, "hero_show_arrows": info.hero_show_arrows,
            "hero_show_dots": info.hero_show_dots}


def editor(request, site):
    if not request.user.has_perm("shop.change_heroslide"):
        return JsonResponse({"error": "No permission"}, status=403)
    context = dict(
        site.each_context(request), title="Hero", subtitle="The big picture at the top of your home page.",
        slides=[slide_json(s) for s in HeroSlide.objects.all()],
        settings=settings_json(StoreInfo.load()),
        brand={"dark": StoreInfo._hex(StoreInfo.load().color_dark, "#161513"), "light": StoreInfo._hex(StoreInfo.load().color_light, "#FAF8F3"),
               "gold": StoreInfo._hex(StoreInfo.load().color_gold, "#B8975A")},
    )
    return render(request, "admin/hero.html", context)


def _is_video(f):
    return f.content_type in VIDEO_TYPES or f.name.lower().endswith((".mp4", ".webm", ".mov"))


def _check(f, video):
    """Raises ValidationError unless the upload is a usable image or video."""
    if video:
        if f.size > MAX_VIDEO_MB * 1024 * 1024:
            raise ValidationError(f"That video is over {MAX_VIDEO_MB} MB. Compress it first.")
    else:
        forms.ImageField().clean(f)      # Pillow checks that it really is a picture
        f.seek(0)


def _put(slide, field, f):
    old = getattr(slide, field)
    if old:
        old.delete(save=False)
    setattr(slide, field, f)


def _clear(slide, *fields):
    for field in fields:
        old = getattr(slide, field)
        if old:
            old.delete(save=False)
        setattr(slide, field, "")


def apply_files(slide, files, post):
    """Desktop upload decides the type. A phone upload is the tall version of the same slide."""
    desktop, phone = files.get("desktop"), files.get("phone")
    if desktop:
        video = _is_video(desktop)
        _check(desktop, video)
        if video:
            _put(slide, "video", desktop)
            slide.kind = HeroSlide.Kind.VIDEO
        else:
            _put(slide, "image", desktop)
            _clear(slide, "video", "video_mobile", "poster")
            slide.kind = HeroSlide.Kind.IMAGE
    if phone:
        video = _is_video(phone)
        if video and slide.kind != HeroSlide.Kind.VIDEO:
            raise ValidationError("A phone video needs a video on desktop too. Upload a phone picture instead.")
        _check(phone, video)
        _put(slide, "video_mobile" if video else "image_mobile", phone)
    if post.get("clear_phone"):
        _clear(slide, "image_mobile", "video_mobile")


def apply_fields(slide, post):
    for key in TEXT:
        if key in post:
            setattr(slide, key, post[key].strip())
    for key in FLAGS:
        if key in post:
            setattr(slide, key, post[key] in ("1", "true", "on"))
    for key in DATES:
        if key in post:
            setattr(slide, key, parse_date(post[key]) if post[key] else None)
    if "seconds" in post:
        raw = post["seconds"].strip()
        if raw and not raw.isdigit():
            raise ValidationError({"seconds": "Use a number between 3 and 20."})
        slide.seconds = int(raw) if raw else None


def _save(slide, request):
    """Applies the posted changes, checks the slide as a whole, saves. Returns the JSON reply."""
    try:
        apply_fields(slide, request.POST)
        apply_files(slide, request.FILES, request.POST)
        if not slide.name:
            slide.name = "Slide"
        slide.full_clean()
    except ValidationError as e:
        errors = e.message_dict if hasattr(e, "error_dict") else {"file": e.messages}
        return JsonResponse({"ok": False, "errors": {k: " ".join(v) for k, v in errors.items()}})
    slide.save()
    return JsonResponse({"ok": True, "slide": slide_json(slide)})


@require_POST
def save_slide(request, pk):
    if not request.user.has_perm("shop.change_heroslide"):
        return JsonResponse({"error": "No permission"}, status=403)
    return _save(get_object_or_404(HeroSlide, pk=pk), request)


@require_POST
def add_slide(request):
    if not request.user.has_perm("shop.add_heroslide"):
        return JsonResponse({"error": "No permission"}, status=403)
    f = request.FILES.get("desktop")
    if not f:
        return JsonResponse({"ok": False, "errors": {"file": "Choose a picture or a video."}})
    last = HeroSlide.objects.order_by("-display_order").first()
    stem = os.path.splitext(f.name)[0].replace("_", " ").replace("-", " ").strip().title()[:100]
    slide = HeroSlide(name=stem or "Slide", display_order=(last.display_order + 1) if last else 0)
    return _save(slide, request)


@require_POST
def delete_slide(request, pk):
    if not request.user.has_perm("shop.delete_heroslide"):
        return JsonResponse({"error": "No permission"}, status=403)
    slide = get_object_or_404(HeroSlide, pk=pk)
    _clear(slide, "image", "image_mobile", "video", "video_mobile", "poster")
    slide.delete()
    return JsonResponse({"ok": True})


@require_POST
def reorder(request):
    if not request.user.has_perm("shop.change_heroslide"):
        return JsonResponse({"error": "No permission"}, status=403)
    try:
        ids = [int(i) for i in json.loads(request.body)["ids"]]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    for position, pk in enumerate(ids):
        HeroSlide.objects.filter(pk=pk).update(display_order=position)
    return JsonResponse({"ok": True})


@require_POST
def save_settings(request):
    if not request.user.has_perm("shop.change_storeinfo"):
        return JsonResponse({"error": "No permission"}, status=403)
    info, post = StoreInfo.load(), request.POST
    for key in SETTING_FLAGS:
        if key in post:
            setattr(info, key, post[key] in ("1", "true", "on"))
    if "hero_transition" in post and post["hero_transition"] in ("slide", "fade"):
        info.hero_transition = post["hero_transition"]
    if "hero_interval" in post:
        if not post["hero_interval"].isdigit() or not 3 <= int(post["hero_interval"]) <= 20:
            return JsonResponse({"ok": False, "errors": {"hero_interval": "Use a number between 3 and 20."}})
        info.hero_interval = int(post["hero_interval"])
    info.save()
    return JsonResponse({"ok": True, "settings": settings_json(info)})
