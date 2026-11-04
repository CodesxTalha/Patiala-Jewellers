"""Products: a clean list to browse and a simple editor to create and change a piece."""
from datetime import timedelta
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from shop.models import Category, Product, ProductImage

from .models import Visit

PER_PAGE = 24
MAX_NEW_PHOTOS = 20
MAX_PHOTO_MB = 12


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "category", "description", "metal", "purity", "weight_grams", "gemstone", "price",
                  "is_featured", "is_active", "image")
        error_messages = {"name": {"required": "Give the piece a name."}, "category": {"required": "Choose a category."}}


def _no_permission():
    return JsonResponse({"error": "No permission"}, status=403)


def listing(request, site):
    if not request.user.has_perm("shop.view_product"):
        return _no_permission()
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    status = request.GET.get("status", "")
    products = Product.objects.select_related("category")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(gemstone__icontains=q))
    if category.isdigit():
        products = products.filter(category_id=int(category))
    if status == "on":
        products = products.filter(is_active=True)
    elif status == "hidden":
        products = products.filter(is_active=False)
    page = Paginator(products, PER_PAGE).get_page(request.GET.get("page"))
    keep = {k: v for k, v in (("q", q), ("category", category), ("status", status)) if v}
    since = timezone.now() - timedelta(days=30)
    seen = {r["path"]: r["n"] for r in Visit.objects.filter(created_at__gte=since, path__in=[f"/collections/{p.slug}/" for p in page]).values("path").annotate(n=Count("id"))}
    for p in page:
        p.views = seen.get(f"/collections/{p.slug}/", 0)
    context = dict(
        site.each_context(request), title="Products", page=page, q=q, category=category, status=status,
        categories=Category.objects.all(), total=Product.objects.count(), filtered=bool(keep),
        base_query=urlencode(keep), status_query={s: urlencode({**{k: v for k, v in keep.items() if k != "status"}, **({"status": s} if s != "all" else {})})
                                                  for s in ("all", "on", "hidden")},
    )
    return render(request, "admin/products.html", context)


def editor(request, site, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    need = "shop.change_product" if product else "shop.add_product"
    if not request.user.has_perm(need):
        return _no_permission()
    title = product.name if product else "New product"
    old_image = product.image.name if product else ""

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        gallery = request.FILES.getlist("gallery")
        ok = form.is_valid()
        if len(gallery) > MAX_NEW_PHOTOS:
            form.add_error(None, f"Add up to {MAX_NEW_PHOTOS} photos at a time.")
            ok = False
        for f in gallery:
            try:
                if f.size > MAX_PHOTO_MB * 1024 * 1024:
                    raise ValidationError(f"“{f.name}” is over {MAX_PHOTO_MB} MB.")
                forms.ImageField().clean(f)
                f.seek(0)
            except ValidationError as e:
                form.add_error(None, e.messages[0])
                ok = False
        if ok:
            obj = form.save(commit=False)
            if request.POST.get("clear_image") and "image" not in request.FILES:
                obj.image = ""
            obj.save()
            if old_image and obj.image.name != old_image:
                default_storage.delete(old_image)
            for g in obj.gallery.filter(pk__in=[i for i in request.POST.getlist("remove_gallery") if i.isdigit()]):
                g.image.delete(save=False)
                g.delete()
            last = obj.gallery.order_by("-display_order").first()
            n = (last.display_order + 1) if last else 0
            for f in gallery:
                ProductImage.objects.create(product=obj, image=f, alt_text=obj.name[:200], display_order=n)
                n += 1
            messages.success(request, f"“{obj.name}” saved.")
            return redirect("admin:product_edit", obj.pk)
    else:
        form = ProductForm(instance=product)

    context = dict(
        site.each_context(request), title=title, product=product, form=form,
        categories=Category.objects.all(), metals=Product.Metal.choices,
        gallery=list(product.gallery.all()) if product else [],
    )
    return render(request, "admin/product_form.html", context)


@require_POST
def delete(request, pk):
    if not request.user.has_perm("shop.delete_product"):
        return _no_permission()
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    for g in product.gallery.all():
        g.image.delete(save=False)
    product.image.delete(save=False)
    product.delete()
    messages.success(request, f"“{name}” deleted.")
    return redirect("admin:products")


@require_POST
def toggle(request, pk):
    """Show or hide a piece, or feature it on the home page, straight from the list."""
    if not request.user.has_perm("shop.change_product"):
        return _no_permission()
    field = request.POST.get("field")
    if field not in ("is_active", "is_featured"):
        return JsonResponse({"ok": False}, status=400)
    product = get_object_or_404(Product, pk=pk)
    setattr(product, field, not getattr(product, field))
    product.save(update_fields=[field, "updated_at"])
    return JsonResponse({"ok": True, "value": getattr(product, field)})
