"""Home page: the sections below the hero as one list you can reorder, switch on and off, add to and edit."""
import json
from urllib.parse import parse_qsl, urlencode, urlsplit

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from shop.context_processors import STORY_IMAGE_FALLBACK
from shop.models import Category, HomeSection, Product

K = HomeSection.Kind
# What can be added: (kind, name, what it is, icon)
KINDS = [
    (K.PRODUCTS, "Products", "A row of pieces. Paste a Collections link, or show your featured pieces.", "gem"),
    (K.COLLECTIONS, "Categories", "A tile for each category.", "grid"),
    (K.SERVICES, "Services", "A row of your services.", "wand"),
    (K.STORY, "Image and text", "A photo beside your words, or behind them. Good for your story or an offer.", "image"),
    (K.LOCATIONS, "Locations", "Your boutiques, with a map.", "pin"),
    (K.CONTACT, "Contact", "Your phone, WhatsApp and email.", "mail"),
]
NAMES = {k: n for k, n, _, _ in KINDS}
MAX_PHOTO_MB = 12
PHOTOS = (("image", "clear_image"), ("image_mobile", "clear_image_mobile"))


def _no_permission():
    return JsonResponse({"error": "No permission"}, status=403)


def _can_edit(request):
    return request.user.has_perm("shop.change_homesection")


def listing(request, site):
    if not request.user.has_perm("shop.view_homesection"):
        return _no_permission()
    sections = list(HomeSection.objects.all())
    for s in sections:
        s.kind_name = NAMES.get(s.kind, s.kind)
    context = dict(site.each_context(request), title="Home page", sections=sections)
    return render(request, "admin/home_sections.html", context)


class HomeSectionForm(forms.ModelForm):
    class Meta:
        model = HomeSection
        fields = ("kind", "label", "title", "text", "link", "button_label", "count", "theme", "cols", "cols_mobile", "layout",
                  "image", "image_mobile", "is_active")
        error_messages = {"title": {"required": "Give the section a heading."}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("count", "theme", "cols", "cols_mobile", "layout"):      # the editor only shows the ones that fit the section
            self.fields[name].required = False

    def clean_count(self):
        n = self.cleaned_data["count"]
        if n is not None and not 1 <= n <= 12:
            raise ValidationError("Choose between 1 and 12.")
        return n

    def _check_photo(self, name):
        f = self.cleaned_data.get(name)
        if f and hasattr(f, "size") and f.size > MAX_PHOTO_MB * 1024 * 1024:
            raise ValidationError(f"That photo is over {MAX_PHOTO_MB} MB.")
        return f

    def clean_image(self):
        return self._check_photo("image")

    def clean_image_mobile(self):
        return self._check_photo("image_mobile")

    def clean(self):
        data = super().clean()
        kind, link = data.get("kind"), (data.get("link") or "").strip()
        if kind == K.SERVICES:
            data["link"] = reverse("shop:services") if data.get("button_label") else ""
        elif kind == K.PRODUCTS and "link" not in self.errors and link:
            parts = urlsplit(link)
            if not parts.path.rstrip("/").endswith(reverse("shop:collections").rstrip("/")):
                self.add_error("link", "This should be a link to your Collections page, like /collections/?category=rings")
                return data
            params = dict(parse_qsl(parts.query))
            if params.get("category") and not Category.objects.filter(slug=params["category"], is_active=True).exists():
                self.add_error("link", f"There is no category called “{params['category']}”.")
                return data
            if params.get("metal") and params["metal"] not in Product.Metal.values:
                self.add_error("link", "The metal in this link is not one we have: " + ", ".join(Product.Metal.values) + ".")
                return data
            data["link"] = reverse("shop:collections") + ("?" + urlencode(params) if params else "")
        elif kind == K.PRODUCTS:
            data["link"] = ""                        # no link: the pieces marked as featured
        elif kind in (K.STORY, K.LOCATIONS, K.CONTACT, K.COLLECTIONS):
            if link and not link.startswith(("/", "http://", "https://", "#", "tel:", "mailto:")):
                self.add_error("link", "A link starts with / or https://")
            data["link"] = link if kind == K.STORY else ""
        return data


def section_editor(request, site, pk=None):
    section = get_object_or_404(HomeSection, pk=pk) if pk else None
    allowed = _can_edit(request) if section else request.user.has_perm("shop.add_homesection")
    if not allowed:
        return _no_permission()
    kind = section.kind if section else (request.POST.get("kind") or request.GET.get("kind"))
    if kind not in NAMES:
        context = dict(site.each_context(request), title="Add a section", kinds=KINDS)
        return render(request, "admin/home_section_new.html", context)
    old = {f: getattr(section, f).name for f, _ in PHOTOS} if section else {}
    if request.method == "POST":
        form = HomeSectionForm(request.POST, request.FILES, instance=section)
        if form.is_valid():
            obj = form.save(commit=False)
            for field, clear in PHOTOS:
                if request.POST.get(clear) and field not in request.FILES:
                    setattr(obj, field, "")
            if not section:
                last = HomeSection.objects.order_by("-display_order").first()
                obj.display_order = (last.display_order + 1) if last else 0
            obj.save()
            for field, name in old.items():
                if name and getattr(obj, field).name != name:
                    default_storage.delete(name)
            messages.success(request, f"“{obj.title}” saved.")
            return redirect("admin:home_section_edit", obj.pk)
    else:
        form = HomeSectionForm(instance=section, initial={"kind": kind, **({} if section else DEFAULT_FOR.get(kind, {}))})
    context = dict(site.each_context(request), title=section.title if section else f"New {NAMES[kind].lower()} section",
                   section=section, form=form, kind=kind, kind_name=NAMES[kind], metals=Product.Metal.choices,
                   categories=Category.objects.filter(is_active=True), story_default=STORY_IMAGE_FALLBACK,
                   layouts=HomeSection.Layout.choices)
    return render(request, "admin/home_section_form.html", context)


# Sensible starting values for a new section of each kind.
DEFAULT_FOR = {
    K.PRODUCTS: {"count": 4, "cols": 4, "cols_mobile": 2, "button_label": ""},
    K.SERVICES: {"count": 4, "cols": 3, "cols_mobile": 1},
    K.COLLECTIONS: {"count": 6},
    K.STORY: {"layout": HomeSection.Layout.LEFT},
}


@require_POST
def section_delete(request, pk):
    if not request.user.has_perm("shop.delete_homesection"):
        return _no_permission()
    section = get_object_or_404(HomeSection, pk=pk)
    name = section.title
    section.image.delete(save=False)
    section.image_mobile.delete(save=False)
    section.delete()
    messages.success(request, f"“{name}” deleted.")
    return redirect("admin:home_sections")


@require_POST
def section_toggle(request, pk):
    if not _can_edit(request):
        return _no_permission()
    section = get_object_or_404(HomeSection, pk=pk)
    section.is_active = not section.is_active
    section.save(update_fields=["is_active"])
    return JsonResponse({"ok": True, "value": section.is_active})


@require_POST
def section_order(request):
    if not _can_edit(request):
        return _no_permission()
    try:
        ids = [int(i) for i in json.loads(request.body)["ids"]]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    for position, pk in enumerate(ids):
        HomeSection.objects.filter(pk=pk).update(display_order=position)
    return JsonResponse({"ok": True})
