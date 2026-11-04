"""Locations: the boutiques. A short list you can reorder, and an editor with a map to place the pin."""
import json

from django import forms
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from shop.models import Branch


class LocationForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ("name", "city", "address", "phone", "opening_hours", "latitude", "longitude", "is_active")
        error_messages = {"name": {"required": "Give the location a name."}}

    def clean_latitude(self):
        value = self.cleaned_data.get("latitude")
        if value is not None and not -90 <= value <= 90:
            raise forms.ValidationError("Latitude is between -90 and 90.")
        return value

    def clean_longitude(self):
        value = self.cleaned_data.get("longitude")
        if value is not None and not -180 <= value <= 180:
            raise forms.ValidationError("Longitude is between -180 and 180.")
        return value

    def clean(self):
        data = super().clean()
        if (data.get("latitude") is None) != (data.get("longitude") is None) and "latitude" not in self.errors and "longitude" not in self.errors:
            self.add_error("longitude" if data.get("latitude") is not None else "latitude", "Set both numbers, or clear both.")
        return data


def _no_permission():
    return JsonResponse({"error": "No permission"}, status=403)


def listing(request, site):
    return redirect(reverse("admin:contact") + "#locations")        # locations live on the Contact page


def editor(request, site, pk=None):
    location = get_object_or_404(Branch, pk=pk) if pk else None
    if not request.user.has_perm("shop.change_branch" if location else "shop.add_branch"):
        return _no_permission()
    title = location.name if location else "New location"
    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            obj = form.save(commit=False)
            if not location:
                last = Branch.objects.order_by("-display_order").first()
                obj.display_order = (last.display_order + 1) if last else 0
            obj.save()
            messages.success(request, f"“{obj.name}” saved.")
            return redirect("admin:location_edit", obj.pk)
    else:
        form = LocationForm(instance=location)
    context = dict(site.each_context(request), title=title, location=location, form=form)
    return render(request, "admin/location_form.html", context)


@require_POST
def delete(request, pk):
    if not request.user.has_perm("shop.delete_branch"):
        return _no_permission()
    location = get_object_or_404(Branch, pk=pk)
    name = location.name
    location.delete()
    messages.success(request, f"“{name}” deleted.")
    return redirect(reverse("admin:contact") + "#locations")


@require_POST
def toggle(request, pk):
    if not request.user.has_perm("shop.change_branch"):
        return _no_permission()
    location = get_object_or_404(Branch, pk=pk)
    location.is_active = not location.is_active
    location.save(update_fields=["is_active"])
    return JsonResponse({"ok": True, "value": location.is_active})


@require_POST
def reorder(request):
    if not request.user.has_perm("shop.change_branch"):
        return _no_permission()
    try:
        ids = [int(i) for i in json.loads(request.body)["ids"]]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    for position, pk in enumerate(ids):
        Branch.objects.filter(pk=pk).update(display_order=position)
    return JsonResponse({"ok": True})
