"""Enquiries: a calm inbox. Filter by status, search, open one to read it, reach the customer, set its status and keep a private note."""
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST

from shop.models import Enquiry

PER_PAGE = 25
STATUSES = Enquiry.Status.choices


def _no_permission():
    return JsonResponse({"error": "No permission"}, status=403)


def _whatsapp_number(phone):
    """Digits for a wa.me link. A local Pakistani number such as 0300 1234567 becomes 92300 1234567."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = "92" + digits[1:]
    return digits


def listing(request, site):
    if not request.user.has_perm("shop.view_enquiry"):
        return _no_permission()
    q, status = request.GET.get("q", "").strip(), request.GET.get("status", "")
    counts = dict(Enquiry.objects.values_list("status").annotate(n=Count("pk")))
    rows = Enquiry.objects.select_related("product")
    if status in dict(STATUSES):
        rows = rows.filter(status=status)
    else:
        status = ""
    if q:
        rows = rows.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q) | Q(message__icontains=q)
                           | Q(product__name__icontains=q))
    keep = {k: v for k, v in (("q", q), ("status", status)) if v}
    page = Paginator(rows, PER_PAGE).get_page(request.GET.get("page"))
    tabs = [("", "All", sum(counts.values()))] + [(v, l, counts.get(v, 0)) for v, l in STATUSES]
    for row in page:
        row.short = " ".join(row.message.split())[:140]
    context = dict(site.each_context(request), title="Enquiries", page=page, q=q, status=status, filtered=bool(q or status), total=sum(counts.values()),
                   tabs=[(v, l, n, urlencode({**{k: x for k, x in keep.items() if k != "status"}, **({"status": v} if v else {})})) for v, l, n in tabs],
                   base_query=urlencode(keep))
    return render(request, "admin/enquiries.html", context)


def detail(request, site, pk):
    if not request.user.has_perm("shop.view_enquiry"):
        return _no_permission()
    enquiry = get_object_or_404(Enquiry.objects.select_related("product"), pk=pk)
    if request.method == "POST":
        if not request.user.has_perm("shop.change_enquiry"):
            return _no_permission()
        if request.POST.get("status") in dict(STATUSES):
            enquiry.status = request.POST["status"]
        enquiry.notes = strip_tags(request.POST.get("notes", "")).strip()[:2000]
        enquiry.save(update_fields=["status", "notes"])
        messages.success(request, "Enquiry saved.")
        return redirect("admin:enquiry", pk)
    wa = _whatsapp_number(enquiry.phone)
    context = dict(site.each_context(request), title=enquiry.name, enquiry=enquiry, statuses=STATUSES, wa=wa)
    return render(request, "admin/enquiry_detail.html", context)


@require_POST
def delete(request, pk):
    if not request.user.has_perm("shop.delete_enquiry"):
        return _no_permission()
    enquiry = get_object_or_404(Enquiry, pk=pk)
    name = enquiry.name
    enquiry.delete()
    messages.success(request, f"The enquiry from {name} was deleted.")
    return redirect("admin:enquiries")
