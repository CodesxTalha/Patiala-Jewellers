"""Settings: brand, contact, social links, colours, fonts and the site-wide switches, on one page with one Save button."""
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import strip_tags

from shop.content import DEFAULTS
from shop.models import ContentBlock, StoreInfo

COLOURS = ("color_light", "color_dark", "color_gold", "color_gold_light", "color_gold_deep", "color_cream")
SOCIALS = ("instagram_url", "facebook_url", "tiktok_url", "youtube_url", "pinterest_url", "x_url")
FONTS = ("font_primary", "heading_weight", "font_secondary", "font_wordmark")
SWITCHES = ("show_preloader", "show_whatsapp_button")
TEXTS = ("whatsapp_message", "whatsapp_label")           # the words of the WhatsApp button, kept with its switch
FILES = (("logo", "clear_logo"), ("favicon", "clear_favicon"))
MAX_FILE_MB = 4


class SettingsForm(forms.ModelForm):
    class Meta:
        model = StoreInfo
        fields = ("name", "descriptor", "tagline", "phone", "whatsapp", "email") + SOCIALS + COLOURS + FONTS
        widgets = {c: forms.TextInput(attrs={"type": "color"}) for c in COLOURS}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("name", "descriptor", "tagline"):
            self.fields[name].required = True
        for name in self.fields:
            self.fields[name].help_text = ""
        for name in SOCIALS:
            self.fields[name].label = name.split("_")[0].title() if name != "x_url" else "X (Twitter)"

    def clean_whatsapp(self):
        digits = "".join(ch for ch in self.cleaned_data["whatsapp"] if ch.isdigit())
        if self.cleaned_data["whatsapp"] and len(digits) < 8:
            raise ValidationError("Use the full number with the country code, for example 923001234567.")
        return digits


def _texts():
    values = {k: DEFAULTS[k][2] for k in TEXTS}
    values.update(dict(ContentBlock.objects.filter(key__in=TEXTS).values_list("key", "text")))
    return values


def editor(request, site):
    if not request.user.has_perm("shop.change_storeinfo"):
        return JsonResponse({"error": "No permission"}, status=403)
    store = StoreInfo.load()
    form, file_errors = SettingsForm(request.POST or None, instance=store), {}
    if request.method == "POST":
        post, old = request.POST, {f: getattr(store, f).name for f, _ in FILES}
        uploads = {}
        for field, clear in FILES:
            f = request.FILES.get(field)
            if f:
                try:
                    if f.size > MAX_FILE_MB * 1024 * 1024:
                        raise ValidationError(f"That file is over {MAX_FILE_MB} MB.")
                    forms.ImageField().clean(f)
                    f.seek(0)
                    uploads[field] = f
                except ValidationError as e:
                    file_errors[field] = e.messages[0]
        if form.is_valid() and not file_errors:
            store = form.save(commit=False)
            for flag in SWITCHES:
                setattr(store, flag, flag in post)
            for field, clear in FILES:
                if field in uploads:
                    setattr(store, field, uploads[field])
                elif post.get(clear):
                    setattr(store, field, "")
            store.save()
            for field, _ in FILES:
                if old[field] and getattr(store, field).name != old[field]:
                    default_storage.delete(old[field])
            for key in TEXTS:
                if key in post:
                    group, label, _ = DEFAULTS[key]
                    block, _ = ContentBlock.objects.get_or_create(key=key, defaults={"group": group, "label": label})
                    block.text = strip_tags(post[key]).strip()[:600]
                    block.save(update_fields=["text"])
            messages.success(request, "Settings saved.")
            return redirect("admin:settings")
        store = StoreInfo.load()
    context = dict(site.each_context(request), title="Settings", form=form, store=store, texts=_texts(), file_errors=file_errors,
                   colours=[form[c] for c in COLOURS[:3]], more_colours=[form[c] for c in COLOURS[3:]],
                   socials=[form[s] for s in SOCIALS])
    return render(request, "admin/settings.html", context)
