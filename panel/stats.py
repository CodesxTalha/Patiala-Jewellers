"""Numbers for the admin dashboard, built from Visit, ClickEvent and Enquiry rows."""
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from shop.models import Branch, Enquiry, HeroSlide, Product, Service, StoreInfo

from .models import ClickEvent, Visit

DEVICE_COLORS = {"mobile": "#161513", "desktop": "#6B6B70", "tablet": "#B5B5BA"}
KIND_LABELS = dict(ClickEvent.Kind.choices)


def _pct_change(now, before):
    if not before:
        return None if not now else 100
    return min(999, round((now - before) * 100 / before))


def _friendly(path, products, services):
    if path == "/":
        return "Home"
    fixed = {"/collections/": "Collections", "/services/": "Services", "/about/": "Our Story",
             "/contact/": "Contact", "/favorites/": "Favorites"}
    if path in fixed:
        return fixed[path]
    parts = [p for p in path.split("/") if p]
    if len(parts) == 2 and parts[0] == "collections":
        return products.get(parts[1], path)
    if len(parts) == 2 and parts[0] == "services":
        return services.get(parts[1], path)
    return path


def ago(moment):
    secs = int((timezone.now() - moment).total_seconds())
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60} min ago"
    if secs < 86400:
        return f"{secs // 3600} h ago"
    return f"{secs // 86400} d ago"


def overview(days=30):
    now = timezone.now()
    today = timezone.localdate()
    start_day = today - timedelta(days=days - 1)
    start = timezone.make_aware(timezone.datetime.combine(start_day, timezone.datetime.min.time()))
    prev_start = start - timedelta(days=days)

    visits = Visit.objects.filter(created_at__gte=start)
    prev_visits = Visit.objects.filter(created_at__gte=prev_start, created_at__lt=start)
    clicks = ClickEvent.objects.filter(created_at__gte=start)
    prev_clicks = ClickEvent.objects.filter(created_at__gte=prev_start, created_at__lt=start)

    visitors = visits.values("visitor").distinct().count()
    prev_visitors = prev_visits.values("visitor").distinct().count()
    views, prev_views = visits.count(), prev_visits.count()
    wa, prev_wa = clicks.filter(kind="whatsapp").count(), prev_clicks.filter(kind="whatsapp").count()
    enq = Enquiry.objects.filter(created_at__gte=start).count()
    prev_enq = Enquiry.objects.filter(created_at__gte=prev_start, created_at__lt=start).count()

    # one bar per day
    per_day = {r["d"]: r for r in visits.annotate(d=TruncDate("created_at")).values("d")
               .annotate(v=Count("id"), u=Count("visitor", distinct=True))}
    series = []
    for i in range(days):
        d = start_day + timedelta(days=i)
        r = per_day.get(d, {"v": 0, "u": 0})
        series.append({"date": d, "views": r["v"], "visitors": r["u"]})
    peak = max([s["views"] for s in series] + [1])
    for s in series:
        s["views_h"] = round(s["views"] * 100 / peak, 1)
        s["visitors_h"] = round(s["visitors"] * 100 / peak, 1)
        s["label"] = f'{s["date"]:%a %d %b}: {s["visitors"]} visitors, {s["views"]} views'
        s["tick"] = f'{s["date"]:%d %b}'

    # devices as a donut (circumference 100)
    dev_rows = list(visits.values("device").annotate(c=Count("id")).order_by("-c"))
    dev_total = sum(r["c"] for r in dev_rows) or 1
    devices, offset = [], 0
    for r in dev_rows:
        pct = r["c"] * 100 / dev_total
        devices.append({"name": r["device"].title(), "count": r["c"], "pct": round(pct), "dash": round(pct, 2),
                        "gap": round(100 - pct, 2), "offset": round(25 - offset, 2),
                        "color": DEVICE_COLORS.get(r["device"], "#B5B5BA")})
        offset += pct

    products = dict(Product.objects.values_list("slug", "name"))
    services = dict(Service.objects.values_list("slug", "name"))
    top_pages_raw = list(visits.values("path").annotate(c=Count("id")).order_by("-c")[:8])
    top_max = max([r["c"] for r in top_pages_raw] + [1])
    top_pages = [{"name": _friendly(r["path"], products, services), "path": r["path"], "count": r["c"],
                  "w": round(r["c"] * 100 / top_max)} for r in top_pages_raw]

    piece_rows = [r for r in visits.filter(path__startswith="/collections/").values("path").annotate(c=Count("id")).order_by("-c")
                  if r["path"].strip("/").count("/") == 1]
    pieces = []
    by_slug = {p.slug: p for p in Product.objects.filter(slug__in=[r["path"].strip("/").split("/")[1] for r in piece_rows[:5]])}
    for r in piece_rows[:5]:
        p = by_slug.get(r["path"].strip("/").split("/")[1])
        if p:
            pieces.append({"name": p.name, "image": p.photo_url, "category": p.category.name if p.category_id else "", "count": r["c"], "url": p.get_absolute_url()})

    kind_rows = list(clicks.values("kind").annotate(c=Count("id")).order_by("-c"))
    kind_max = max([r["c"] for r in kind_rows] + [1])
    click_kinds = [{"name": KIND_LABELS.get(r["kind"], r["kind"]), "count": r["c"], "w": round(r["c"] * 100 / kind_max)} for r in kind_rows]
    top_clicks = [{"kind": KIND_LABELS.get(r["kind"], r["kind"]), "label": r["label"] or "-", "count": r["c"]}
                  for r in clicks.values("kind", "label").annotate(c=Count("id")).order_by("-c")[:6]]

    ref_rows = list(visits.exclude(referrer="").values("referrer").annotate(c=Count("id")).order_by("-c")[:6])
    ref_max = max([r["c"] for r in ref_rows] + [1])
    referrers = [{"name": r["referrer"], "count": r["c"], "w": round(r["c"] * 100 / ref_max)} for r in ref_rows]

    def mark(rows):
        for r in rows:
            r.when = ago(r.created_at)
            r.short = r.visitor[:6]
            r.where = "Local" if r.ip in ("127.0.0.1", "::1", None, "") else r.ip
        return rows

    live = Visit.objects.filter(created_at__gte=now - timedelta(minutes=5)).values("visitor").distinct().count()
    latest_visits = mark(list(Visit.objects.all()[:10]))
    latest_clicks = mark(list(ClickEvent.objects.all()[:8]))
    for r in latest_visits:
        r.name = _friendly(r.path, products, services)

    return {
        "days": days, "tick_step": 1 if days <= 7 else 5 if days <= 30 else 15,
        "cards": [
            {"label": "Visitors", "value": visitors, "change": _pct_change(visitors, prev_visitors), "icon": "users"},
            {"label": "Page views", "value": views, "change": _pct_change(views, prev_views), "icon": "eye"},
            {"label": "WhatsApp taps", "value": wa, "change": _pct_change(wa, prev_wa), "icon": "chat"},
            {"label": "Enquiries", "value": enq, "change": _pct_change(enq, prev_enq), "icon": "mail"},
        ],
        "series": series, "peak": peak, "devices": devices, "device_total": dev_total if dev_rows else 0,
        "top_pages": top_pages, "pieces": pieces, "click_kinds": click_kinds, "top_clicks": top_clicks,
        "referrers": referrers, "live": live, "latest_visits": latest_visits, "latest_clicks": latest_clicks,
        "new_enquiries": list(Enquiry.objects.filter(status="new").select_related("product")[:5]),
        "new_enquiry_count": Enquiry.objects.filter(status="new").count(),
        "has_data": views > 0 or ClickEvent.objects.exists(),
    }


def setup_checklist():
    """A short list of what is still missing before the site is ready to share."""
    s = StoreInfo.load()
    items = [
        ("Add your WhatsApp number", bool(s.whatsapp), "admin:settings"),
        ("Add your phone and email", bool(s.phone and s.email), "admin:settings"),
        ("Upload your logo", bool(s.logo), "admin:settings"),
        ("Add a social link", bool(s.socials), "admin:settings"),
        ("Add a hero slide", HeroSlide.objects.filter(is_active=True).exists(), "admin:hero"),
        ("Pin every boutique on the map", not Branch.objects.filter(is_active=True, latitude__isnull=True).exists()
         and Branch.objects.exists(), "admin:locations"),
        ("Add at least one product", Product.objects.filter(is_active=True).exists(), "admin:product_new"),
        ("Add a service", Service.objects.filter(is_active=True).exists(), "admin:service_new"),
    ]
    done = sum(1 for _, ok, _ in items if ok)
    return {"items": [{"label": l, "ok": ok, "url": u} for l, ok, u in items], "done": done, "total": len(items),
            "pct": round(done * 100 / len(items))}
