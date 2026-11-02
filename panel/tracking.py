"""Visitor and click tracking for the public site. First-party only: nothing is sent to another service."""
import re
import uuid
from urllib.parse import urlparse

from .models import Visit

COOKIE = "pj_vid"
ONE_YEAR = 60 * 60 * 24 * 365
SKIP = ("/admin", "/static", "/media", "/t/", "/favicon", "/robots.txt")
BOT = re.compile(r"bot|crawl|spider|slurp|preview|headless|lighthouse|monitor|curl|wget|python-requests|facebookexternalhit", re.I)


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")


def device_of(ua):
    ua = ua.lower()
    if "ipad" in ua or "tablet" in ua:
        return "tablet"
    if "mobi" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    return "desktop"


def browser_of(ua):
    for needle, name in (("edg", "Edge"), ("opr", "Opera"), ("firefox", "Firefox"), ("chrome", "Chrome"), ("safari", "Safari")):
        if needle in ua.lower():
            return name
    return "Other"


def visitor_id(request):
    vid = request.COOKIES.get(COOKIE, "")
    return vid if re.fullmatch(r"[0-9a-f]{32}", vid) else ""


class TrackingMiddleware:
    """Counts each page view of the public site and gives every browser an anonymous id cookie."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self.record(request, response)
        except Exception:      # tracking must never break a page
            pass
        return response

    def record(self, request, response):
        path = request.path
        if request.method != "GET" or response.status_code != 200 or path.startswith(SKIP):
            return
        if "text/html" not in response.get("Content-Type", ""):
            return
        ua = request.META.get("HTTP_USER_AGENT", "")
        if not ua or BOT.search(ua) or request.META.get("HTTP_SEC_PURPOSE", "").startswith("prefetch"):
            return
        vid = visitor_id(request)
        if not vid:
            vid = uuid.uuid4().hex
            response.set_cookie(COOKIE, vid, max_age=ONE_YEAR, samesite="Lax", httponly=True)
        ref = urlparse(request.META.get("HTTP_REFERER", "")).netloc
        Visit.objects.create(
            visitor=vid, path=path[:300], referrer="" if ref == request.get_host() else ref[:200],
            device=device_of(ua), browser=browser_of(ua), ip=client_ip(request),
        )
