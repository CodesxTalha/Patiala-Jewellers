from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EnquiryForm
from .models import Branch, Category, Product


def visible_products():
    return (
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .prefetch_related("gallery")
    )


def home(request):
    return render(request, "shop/home.html", {
        "featured": visible_products().filter(is_featured=True)[:8],
        "categories": Category.objects.filter(is_active=True)[:6],
    })


def collections(request):
    products = visible_products()
    current = None

    slug = request.GET.get("category")
    if slug:
        current = get_object_or_404(Category, slug=slug, is_active=True)
        products = products.filter(category=current)

    metal = request.GET.get("metal")
    if metal in Product.Metal.values:
        products = products.filter(metal=metal)

    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(gemstone__icontains=q))

    page = Paginator(products, 12).get_page(request.GET.get("page"))

    # Query string without "page", for the pagination links.
    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "shop/collections.html", {
        "page_obj": page,
        "current_category": current,
        "current_metal": metal,
        "metals": Product.Metal.choices,
        "q": q,
        "query": params.urlencode(),
    })


def product_detail(request, slug):
    product = get_object_or_404(visible_products(), slug=slug)
    form = EnquiryForm(request.POST or None, initial={"message": f"I am interested in {product.name}."})

    if request.method == "POST" and form.is_valid():
        enquiry = form.save(commit=False)
        enquiry.product = product
        enquiry.save()
        messages.success(request, "Thank you. We will be in touch shortly.")
        return redirect(product.get_absolute_url())

    related = visible_products().filter(category=product.category).exclude(pk=product.pk)[:4]
    return render(request, "shop/product_detail.html", {
        "product": product,
        "photos": product.photo_urls,
        "related": related,
        "form": form,
        "wa_message": f"Hello, I am interested in {product.name}. {request.build_absolute_uri()}",
    })


def favorites(request):
    # All pieces as JSON; the page filters them by the slugs saved in the visitor's browser.
    pieces = [
        {
            "slug": p.slug, "name": p.name, "category": p.category.name,
            "image": p.photo_url, "url": request.build_absolute_uri(p.get_absolute_url()),
            "path": p.get_absolute_url(), "price": p.price_label,
        }
        for p in visible_products()
    ]
    return render(request, "shop/favorites.html", {"pieces": pieces})


def about(request):
    return render(request, "shop/about.html")


def contact(request):
    form = EnquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thank you. We will be in touch shortly.")
        return redirect("shop:contact")

    # Boutique positions for the map (only those with coordinates).
    points = [
        {
            "id": b.pk, "name": b.name, "address": b.address,
            "lat": float(b.latitude), "lng": float(b.longitude),
        }
        for b in Branch.objects.filter(is_active=True, latitude__isnull=False, longitude__isnull=False)
    ]
    return render(request, "shop/contact.html", {"form": form, "points": points})
