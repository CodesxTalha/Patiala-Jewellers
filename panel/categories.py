"""Categories: a short list you can reorder by dragging, and a small editor."""
import json

from django import forms
from django.contrib import messages
from django.core.files.storage import default_storage
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from shop.models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description", "is_active", "image")
        error_messages = {"name": {"required": "Give the category a name.", "unique": "There is already a category with this name."}}


def _no_permission():
    return JsonResponse({"error": "No permission"}, status=403)


def listing(request, site):
    if not request.user.has_perm("shop.view_category"):
        return _no_permission()
    categories = Category.objects.annotate(n=Count("products"))
    context = dict(site.each_context(request), title="Categories", categories=categories)
    return render(request, "admin/categories.html", context)


def editor(request, site, pk=None):
    category = get_object_or_404(Category.objects.annotate(n=Count("products")), pk=pk) if pk else None
    if not request.user.has_perm("shop.change_category" if category else "shop.add_category"):
        return _no_permission()
    title = category.name if category else "New category"
    old_image = category.image.name if category else ""
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            obj = form.save(commit=False)
            if request.POST.get("clear_image") and "image" not in request.FILES:
                obj.image = ""
            if not category:
                last = Category.objects.order_by("-display_order").first()
                obj.display_order = (last.display_order + 1) if last else 0
            obj.save()
            if old_image and obj.image.name != old_image:
                default_storage.delete(old_image)
            messages.success(request, f"“{obj.name}” saved.")
            return redirect("admin:category_edit", obj.pk)
    else:
        form = CategoryForm(instance=category)
    context = dict(site.each_context(request), title=title, category=category, form=form)
    return render(request, "admin/category_form.html", context)


@require_POST
def delete(request, pk):
    if not request.user.has_perm("shop.delete_category"):
        return _no_permission()
    category = get_object_or_404(Category, pk=pk)
    if category.products.exists():       # pieces always belong to a category, so it has to be empty first
        messages.error(request, f"“{category.name}” still has pieces in it. Move or delete them first.")
        return redirect("admin:category_edit", pk)
    name = category.name
    category.image.delete(save=False)
    category.delete()
    messages.success(request, f"“{name}” deleted.")
    return redirect("admin:categories")


@require_POST
def toggle(request, pk):
    if not request.user.has_perm("shop.change_category"):
        return _no_permission()
    category = get_object_or_404(Category, pk=pk)
    category.is_active = not category.is_active
    category.save(update_fields=["is_active"])
    return JsonResponse({"ok": True, "value": category.is_active})


@require_POST
def reorder(request):
    if not request.user.has_perm("shop.change_category"):
        return _no_permission()
    try:
        ids = [int(i) for i in json.loads(request.body)["ids"]]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    for position, pk in enumerate(ids):
        Category.objects.filter(pk=pk).update(display_order=position)
    return JsonResponse({"ok": True})
