
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EnquiryForm
from .content import DEFAULTS
from .models import AboutValue, Branch, Category, ContentBlock, HeroSlide, HomeSection, Product, Service, StoreInfo


def content_text(key):
    block = ContentBlock.objects.filter(key=key).first()
    return block.text if block else DEFAULTS[key][2]


def visible_products():
    return (
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .prefetch_related("gallery")
    )


def hero_slides():
    """Active slides inside their date window that have a picture or video to show."""
    today = timezone.localdate()
    slides = HeroSlide.objects.filter(is_active=True).filter(
        Q(show_from__isnull=True) | Q(show_from__lte=today), Q(show_until__isnull=True) | Q(show_until__gte=today)
    )
    return [sl for sl in slides if sl.desktop_url]


def boutique_map():
    """Pin positions for the maps. When there is exactly one location, `solo` is it: the pages then show one big map."""
    active = list(Branch.objects.filter(is_active=True))
    points = [
        {"id": b.pk, "name": b.name, "address": b.address, "lat": float(b.latitude), "lng": float(b.longitude)}
        for b in active if b.latitude is not None and b.longitude is not None
    ]
    solo = active[0] if len(active) == 1 and points else None
    return {"points": points, "solo": solo}


def home_blocks(store, points):
    """The home page sections in their saved order, each with what it needs to draw itself. Empty ones are left out."""
    blocks = []
    for sec in HomeSection.objects.filter(is_active=True):
        kind, items = sec.kind, []
        if kind == HomeSection.Kind.PRODUCTS:
            try:
                products = filter_products(sec.params)[0] if sec.link else visible_products().filter(is_featured=True)
                items = list(products[:sec.count])
            except Http404:          # the category in the link no longer exists
                items = []
        elif kind == HomeSection.Kind.SERVICES:
            items = list(Service.objects.filter(is_active=True)[:sec.count])
        elif kind == HomeSection.Kind.COLLECTIONS:
            items = list(Category.objects.filter(is_active=True)[:sec.count])
        elif kind == HomeSection.Kind.LOCATIONS:
            items = [1] if points["points"] or Branch.objects.filter(is_active=True).exists() else []
        elif kind == HomeSection.Kind.CONTACT:
            items = [1] if (store.phone or store.whatsapp or store.email) else []
        else:
            items = [1]
        if items:
            blocks.append({"s": sec, "items": items, "template": f"shop/home/_{kind}.html"})
    return blocks


def home(request):
    points = boutique_map()
    store = StoreInfo.load()
    blocks = home_blocks(store, points)
    return render(request, "shop/home.html", {
        "slides": hero_slides(),
        "blocks": blocks,
        "has_map": bool(points["solo"]) and any(b["s"].kind == HomeSection.Kind.LOCATIONS for b in blocks),
        **points,
    })


def filter_products(params):
    """Apply the Collections page filters (category, metal, q). Returns the products and the chosen category."""
    products = visible_products()
    current = None
    slug = params.get("category")
    if slug:
        current = get_object_or_404(Category, slug=slug, is_active=True)
        products = products.filter(category=current)
    metal = params.get("metal")
    if metal in Product.Metal.values:
        products = products.filter(metal=metal)
    q = params.get("q", "").strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(gemstone__icontains=q))
    return products, current


def collections(request):
    products, current = filter_products(request.GET)
    metal = request.GET.get("metal")
    q = request.GET.get("q", "").strip()

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

    return render(request, "shop/contact.html", {"form": form, **boutique_map()})
