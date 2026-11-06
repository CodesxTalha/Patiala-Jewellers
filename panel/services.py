"""Services: a short list you can reorder by dragging, and an editor with simple lists for what is included and the steps."""
import json

from django import forms
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from shop.models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "summary", "intro", "description", "includes", "process", "turnaround", "price_note", "is_active", "image", "wide_image")
        error_messages = {
            "name": {"required": "Give the service a name.", "unique": "There is already a service with this name."},
            "summary": {"required": "Add one short line. It shows on the service cards."},
        }


def _no_permission():
    return JsonResponse({"error": "No permission"}, status=403)


def _unique_slug(name, pk=None):
    base = slugify(name) or "service"
    slug, n = base, 2
    while Service.objects.filter(slug=slug).exclude(pk=pk).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def listing(request, site):
    if not request.user.has_perm("shop.view_service"):
        return _no_permission()
    context = dict(site.each_context(request), title="Services", services=Service.objects.all())
    return render(request, "admin/services.html", context)


def editor(request, site, pk=None):
    service = get_object_or_404(Service, pk=pk) if pk else None
    if not request.user.has_perm("shop.change_service" if service else "shop.add_service"):
        return _no_permission()
    title = service.name if service else "New service"
    old_files = [f.name for f in (service.image, service.wide_image) if f] if service else []
    if request.method == "POST":
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            obj = form.save(commit=False)
            if request.POST.get("clear_image") and "image" not in request.FILES:
                obj.image = ""
            if request.POST.get("clear_wide_image") and "wide_image" not in request.FILES:
                obj.wide_image = ""
            if not service:
                last = Service.objects.order_by("-display_order").first()
                obj.display_order = (last.display_order + 1) if last else 0
                obj.slug = _unique_slug(obj.name)
            obj.save()
            kept = {f.name for f in (obj.image, obj.wide_image) if f}
            for name in old_files:
                if name not in kept:
                    default_storage.delete(name)
            messages.success(request, f"“{obj.name}” saved.")
            return redirect("admin:service_edit", obj.pk)
        source = {"include_list": [l.strip() for l in (form.data.get("includes") or "").splitlines() if l.strip()],
                  "step_list": [{"title": t.partition("|")[0].strip(), "text": t.partition("|")[2].strip()}
                                for t in (form.data.get("process") or "").splitlines() if t.strip()]}
    else:
        form = ServiceForm(instance=service)
        source = {"include_list": service.include_list if service else [], "step_list": service.step_list if service else []}
    context = dict(site.each_context(request), title=title, service=service, form=form, lists=source)
    return render(request, "admin/service_form.html", context)


@require_POST
def delete(request, pk):
    if not request.user.has_perm("shop.delete_service"):
        return _no_permission()
    service = get_object_or_404(Service, pk=pk)
    name = service.name
    service.image.delete(save=False)
    service.wide_image.delete(save=False)
    service.delete()
    messages.success(request, f"“{name}” deleted.")
    return redirect("admin:services")


@require_POST
def toggle(request, pk):
    if not request.user.has_perm("shop.change_service"):
        return _no_permission()
    service = get_object_or_404(Service, pk=pk)
    service.is_active = not service.is_active
    service.save(update_fields=["is_active"])
    return JsonResponse({"ok": True, "value": service.is_active})


@require_POST
def reorder(request):
    if not request.user.has_perm("shop.change_service"):
        return _no_permission()
    try:
        ids = [int(i) for i in json.loads(request.body)["ids"]]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    for position, pk in enumerate(ids):
        Service.objects.filter(pk=pk).update(display_order=position)
    return JsonResponse({"ok": True})
