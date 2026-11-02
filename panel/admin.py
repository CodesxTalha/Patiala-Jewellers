from django.contrib import admin

from shop.models import Enquiry

from .models import ClickEvent, Visit


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "product", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "created_at")
    search_fields = ("name", "phone", "email", "message")
    readonly_fields = ("name", "phone", "email", "message", "product", "created_at")
    fields = ("name", "phone", "email", "product", "message", "created_at", "status", "notes")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False  # enquiries come from the website only


class ReadOnlyLog(admin.ModelAdmin):
    """Visitor and click logs: look, filter and clear, never edit."""
    list_per_page = 40

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Visit)
class VisitAdmin(ReadOnlyLog):
    list_display = ("when", "path", "device", "browser", "where", "who", "referrer")
    list_filter = ("device", "browser")
    search_fields = ("path", "ip", "referrer", "visitor")
    date_hierarchy = "created_at"

    @admin.display(description="When", ordering="created_at")
    def when(self, obj):
        return obj.created_at

    @admin.display(description="Where from")
    def where(self, obj):
        return "Local" if obj.ip in ("127.0.0.1", "::1", None) else obj.ip

    @admin.display(description="Visitor")
    def who(self, obj):
        return obj.visitor[:6]


@admin.register(ClickEvent)
class ClickEventAdmin(ReadOnlyLog):
    list_display = ("when", "kind", "label", "path", "where", "who")
    list_filter = ("kind",)
    search_fields = ("label", "target", "path", "ip")
    date_hierarchy = "created_at"

    @admin.display(description="When", ordering="created_at")
    def when(self, obj):
        return obj.created_at

    @admin.display(description="Where from")
    def where(self, obj):
        return "Local" if obj.ip in ("127.0.0.1", "::1", None) else obj.ip

    @admin.display(description="Visitor")
    def who(self, obj):
        return obj.visitor[:6]
