from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EnquiryForm
from .content import DEFAULTS
from .models import AboutValue, Branch, Category, ContentBlock, Product, Service


def content_text(key):
    block = ContentBlock.objects.filter(key=key).first()
    return block.text if block else DEFAULTS[key][2]


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
        "services": Service.objects.filter(is_active=True)[:4],
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
        messages.success(request, content_text("contact_thanks"))
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


def services(request):
    return render(request, "shop/services.html", {"services": Service.objects.filter(is_active=True)})


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    others = Service.objects.filter(is_active=True).exclude(pk=service.pk)[:3]
    return render(request, "shop/service_detail.html", {"service": service, "others": others})


def about(request):
    return render(request, "shop/about.html", {"values": AboutValue.objects.filter(is_active=True)})


def contact(request):
    form = EnquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, content_text("contact_thanks"))
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
