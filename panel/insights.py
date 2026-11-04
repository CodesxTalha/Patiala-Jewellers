"""Visitors and Clicks: two reports in plain words. Pick a period, filter by page or device, see which pages and pieces people look at."""
import re
from datetime import timedelta
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from shop.models import Product, Service

from .models import ClickEvent, Visit
from .stats import KIND_LABELS, _friendly, ago

PERIODS = (7, 30, 90)
PIECE_PATH = r"^/collections/[^/]+/$"
SECTIONS = [("home", "Home"), ("collections", "Collections"), ("pieces", "Piece pages"), ("services", "Services"),
            ("about", "About"), ("contact", "Contact"), ("favorites", "Favorites")]
DEVICES = [("mobile", "Phone"), ("desktop", "Computer"), ("tablet", "Tablet")]
WHERE = {"home": Q(path="/"), "collections": Q(path="/collections/"), "pieces": Q(path__regex=PIECE_PATH),
         "services": Q(path__startswith="/services/"), "about": Q(path="/about/"), "contact": Q(path="/contact/"),
         "favorites": Q(path="/favorites/")}


def section_of(path):
    if path == "/":
        return "Home"
    if re.match(PIECE_PATH, path):
        return "Piece pages"
    for key, label in SECTIONS:
        if key in ("collections", "services", "about", "contact", "favorites") and (path == f"/{key}/" or (key == "services" and path.startswith("/services/"))):
            return label
    return "Other"


def _start(days):
    day = timezone.localdate() - timedelta(days=days - 1)
    return timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))


def _params(request, extra=()):
    days = int(request.GET["days"]) if request.GET.get("days", "").isdigit() and int(request.GET["days"]) in PERIODS else 30
    out = {"days": days}
    for key in extra:
        out[key] = request.GET.get(key, "").strip()
    return out


def _names():
    return dict(Product.objects.values_list("slug", "name")), dict(Service.objects.values_list("slug", "name"))


def _tab_links(base, key, options, current):
    """Links for a row of tabs: each one keeps the other filters and swaps in its own value."""
    rest = {k: v for k, v in base.items() if k != key and v not in ("", None)}
    return [{"value": v, "label": l, "n": n, "on": current == v, "query": urlencode({**rest, **({key: v} if v else {})})} for v, l, n in options]


def _no_permission():
    return JsonResponse({"error": "No permission"}, status=403)


def visitors(request, site):
    if not request.user.has_perm("panel.view_visit"):
        return _no_permission()
    p = _params(request, ("view", "section", "device", "q"))
    view = p["view"] if p["view"] in ("pages", "pieces", "recent") else "pages"
    section = p["section"] if p["section"] in dict(SECTIONS) else ""
    device = p["device"] if p["device"] in dict(DEVICES) else ""
    q = p["q"].lower()
    rows = Visit.objects.filter(created_at__gte=_start(p["days"]))
    if device:
        rows = rows.filter(device=device)
    scoped = rows.filter(WHERE[section]) if section else rows
    products, services = _names()
    total_views, total_visitors = scoped.count(), scoped.values("visitor").distinct().count()
    mobile = scoped.filter(device="mobile").count()
    summary = [("Visitors", total_visitors), ("Page views", total_views),
               ("Pages per visitor", round(total_views / total_visitors, 1) if total_visitors else 0),
               ("On a phone", f"{round(mobile * 100 / total_views)}%" if total_views else "-")]
    context = dict(site.each_context(request), title="Visitors", p=p, view=view, section=section, device=device, q=p["q"], summary=summary,
                   sections=SECTIONS, devices=DEVICES, periods=PERIODS)
    base = {"days": p["days"], "view": view, "section": section, "device": device, "q": p["q"]}
    context["view_tabs"] = _tab_links(base, "view",
                                      [("pages", "Pages", None), ("pieces", "Pieces", None), ("recent", "Recent visits", None)], view)
    context["hidden"] = {k: v for k, v in base.items() if k in ("view", "section", "device", "q") and v}
    context["period_links"] = [{"days": d, "on": d == p["days"], "query": urlencode({**{k: v for k, v in base.items() if v and k != "days"}, "days": d})} for d in PERIODS]
    context["clear"] = bool(section or device or q)

    if view == "pages":
        agg = list(scoped.values("path").annotate(v=Count("id"), u=Count("visitor", distinct=True)).order_by("-v")[:300])
        items = [{"name": _friendly(r["path"], products, services), "path": r["path"], "section": section_of(r["path"]), "views": r["v"], "visitors": r["u"]} for r in agg]
        if q:
            items = [i for i in items if q in i["name"].lower() or q in i["path"].lower()]
        peak = max([i["views"] for i in items] + [1])
        for i in items:
            i["w"] = round(i["views"] * 100 / peak)
        context["items"] = items[:100]
    elif view == "pieces":
        agg = {r["path"].strip("/").split("/")[1]: r for r in rows.filter(path__regex=PIECE_PATH).values("path").annotate(v=Count("id"), u=Count("visitor", distinct=True))}
        saves = {r["label"]: r["c"] for r in ClickEvent.objects.filter(created_at__gte=_start(p["days"]), kind="favorite").values("label").annotate(c=Count("id"))}
        items = []
        for pr in Product.objects.select_related("category"):
            a = agg.get(pr.slug, {"v": 0, "u": 0})
            items.append({"name": pr.name, "category": pr.category.name if pr.category_id else "", "image": pr.photo_url, "views": a["v"], "visitors": a["u"],
                          "saved": saves.get(pr.slug, 0), "hidden": not pr.is_active, "edit": pr.pk})
        if q:
            items = [i for i in items if q in i["name"].lower() or q in i["category"].lower()]
        items.sort(key=lambda i: (-i["views"], -i["saved"], i["name"].lower()))
        peak = max([i["views"] for i in items] + [1])
        for i in items:
            i["w"] = round(i["views"] * 100 / peak)
        context["items"] = items
    else:
        page = Paginator(scoped, 30).get_page(request.GET.get("page"))
        for r in page:
            r.name, r.section = _friendly(r.path, products, services), section_of(r.path)
            r.when = ago(r.created_at)
            r.device_label = dict(DEVICES).get(r.device, r.device.title())
            r.from_ = r.referrer or "Direct"
        context["page"] = page
        context["base_query"] = urlencode({k: v for k, v in base.items() if v and k != "view"} | {"view": "recent"})
    return render(request, "admin/visitors.html", context)


def clicks(request, site):
    if not request.user.has_perm("panel.view_clickevent"):
        return _no_permission()
    p = _params(request, ("view", "kind", "section"))
    view = p["view"] if p["view"] in ("summary", "recent") else "summary"
    kind = p["kind"] if p["kind"] in KIND_LABELS else ""
    section = p["section"] if p["section"] in dict(SECTIONS) else ""
    rows = ClickEvent.objects.filter(created_at__gte=_start(p["days"]))
    if section:
        rows = rows.filter(WHERE[section])
    counts = dict(rows.values_list("kind").annotate(n=Count("id")))
    scoped = rows.filter(kind=kind) if kind else rows
    products, services = _names()
    base = {"days": p["days"], "view": view, "kind": kind, "section": section}
    kinds = [("", "All", sum(counts.values()))] + [(k, l, counts[k]) for k, l in ClickEvent.Kind.choices if counts.get(k)]
    context = dict(site.each_context(request), title="Clicks", p=p, view=view, kind=kind, section=section, sections=SECTIONS, periods=PERIODS,
                   total=scoped.count(), people=scoped.values("visitor").distinct().count())
    context["kind_tabs"] = _tab_links(base, "kind", kinds, kind)
    context["view_tabs"] = _tab_links(base, "view", [("summary", "What was tapped", None), ("recent", "Recent taps", None)], view)
    context["hidden"] = {k: v for k, v in base.items() if k in ("view", "kind", "section") and v}
    context["period_links"] = [{"days": d, "on": d == p["days"], "query": urlencode({**{k: v for k, v in base.items() if v and k != "days"}, "days": d})} for d in PERIODS]
    context["clear"] = bool(kind or section)
    context["kind_label"] = KIND_LABELS.get(kind, "")

    def label_of(kind_, label, target):
        if kind_ == "favorite":
            return products.get(label, label or "A piece")
        return label or target or "-"

    if view == "summary":
        agg = list(scoped.values("kind", "label").annotate(n=Count("id"), u=Count("visitor", distinct=True)).order_by("-n")[:200])
        items = [{"name": label_of(r["kind"], r["label"], ""), "kind": KIND_LABELS.get(r["kind"], r["kind"]), "taps": r["n"], "visitors": r["u"]} for r in agg]
        peak = max([i["taps"] for i in items] + [1])
        for i in items:
            i["w"] = round(i["taps"] * 100 / peak)
        context["items"] = items
    else:
        page = Paginator(scoped, 30).get_page(request.GET.get("page"))
        for r in page:
            r.name, r.kind_label, r.when = label_of(r.kind, r.label, r.target), KIND_LABELS.get(r.kind, r.kind), ago(r.created_at)
            r.on_page = _friendly(r.path, products, services) if r.path else "-"
        context["page"] = page
        context["base_query"] = urlencode({k: v for k, v in base.items() if v and k != "view"} | {"view": "recent"})
    return render(request, "admin/clicks.html", context)
