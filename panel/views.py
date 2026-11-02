import json
import uuid

from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import ClickEvent
from .tracking import COOKIE, ONE_YEAR, client_ip, visitor_id


@csrf_exempt
@require_POST
def track_click(request):
    """Counts a tap on WhatsApp, a phone number, a social link, a hero slide and so on."""
    try:
        data = json.loads(request.body[:2000] or b"{}")
    except ValueError:
        return HttpResponse(status=400)
    kind = data.get("kind")
    if kind not in ClickEvent.Kind.values:
        return HttpResponse(status=400)
    vid = visitor_id(request)
    new_cookie = not vid
    vid = vid or uuid.uuid4().hex
    since = timezone.now() - timezone.timedelta(hours=1)
    if ClickEvent.objects.filter(visitor=vid, created_at__gte=since).count() < 200:   # a cap against floods
        ClickEvent.objects.create(
            visitor=vid, kind=kind, label=str(data.get("label", ""))[:120], target=str(data.get("target", ""))[:300],
            path=str(data.get("path", ""))[:300], ip=client_ip(request),
        )
    response = HttpResponse(status=204)
    if new_cookie:
        response.set_cookie(COOKIE, vid, max_age=ONE_YEAR, samesite="Lax", httponly=True)
    return response
