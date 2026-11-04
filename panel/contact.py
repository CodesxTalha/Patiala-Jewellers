"""Contact: everything about the Contact page in one place: its top, your phone, email and WhatsApp, social links, the form's words and the locations."""
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import strip_tags

from shop.content import DEFAULTS
from shop.models import Branch, ContentBlock, StoreInfo

SOCIALS = ("instagram_url", "facebook_url", "tiktok_url", "youtube_url", "pinterest_url", "x_url")
TEXTS = ("contact_label", "contact_title", "contact_lead", "contact_direct_title", "contact_form_title", "contact_thanks")


class ContactForm(forms.ModelForm):
    class Meta:
        model = StoreInfo
        fields = ("phone", "email", "whatsapp") + SOCIALS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            self.fields[name].help_text = ""
        for name in SOCIALS:
            self.fields[name].label = {"x_url": "X (Twitter)", "tiktok_url": "TikTok", "youtube_url": "YouTube"}.get(name, name.split("_")[0].title())

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
    form = ContactForm(request.POST or None, instance=StoreInfo.load())
    if request.method == "POST" and form.is_valid():
        form.save()
        for key in TEXTS:
            if key in request.POST:
                group, label, _ = DEFAULTS[key]
                block, _ = ContentBlock.objects.get_or_create(key=key, defaults={"group": group, "label": label})
                block.text = strip_tags(request.POST[key]).strip()[:600]
                block.save(update_fields=["text"])
        messages.success(request, "Contact page saved.")
        return redirect("admin:contact")
    can_edit_locations = request.user.has_perm("shop.view_branch")
    context = dict(site.each_context(request), title="Contact", form=form, texts=_texts(), socials=[form[s] for s in SOCIALS],
                   locations=Branch.objects.all() if can_edit_locations else [], can_edit_locations=can_edit_locations)
    return render(request, "admin/contact.html", context)
