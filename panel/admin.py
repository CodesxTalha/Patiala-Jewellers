from django import forms
from django.contrib import admin

from shop.models import ContentBlock, Enquiry, StoreInfo

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


COLOR_FIELDS = ("color_light", "color_dark", "color_gold", "color_gold_light", "color_gold_deep", "color_cream")


class StoreInfoForm(forms.ModelForm):
    class Meta:
        model = StoreInfo
        fields = "__all__"
        widgets = {name: forms.TextInput(attrs={"type": "color", "style": "width:5rem;height:2.2rem;padding:2px;"})
                   for name in COLOR_FIELDS}


@admin.register(StoreInfo)
class StoreInfoAdmin(admin.ModelAdmin):
    form = StoreInfoForm
    fieldsets = (
        ("Brand", {"fields": ("name", "descriptor", "tagline")}),
        ("Contact", {"fields": ("phone", "whatsapp", "email")}),
        ("Social media", {"fields": ("instagram_url", "facebook_url", "tiktok_url", "youtube_url", "pinterest_url", "x_url")}),
        ("Colours", {"fields": COLOR_FIELDS,
                     "description": "Light is about 60% of the site, dark about 30% and gold about 10%."}),
        ("Fonts", {"fields": ("font_primary", "heading_weight", "font_secondary", "font_wordmark")}),
        ("Logo", {"fields": ("logo", "favicon")}),
        ("Show or hide", {"fields": ("show_preloader", "show_whatsapp_button")}),
    )

    def has_add_permission(self, request):
        return not StoreInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Skip the list page and go straight to editing the single record.
        from django.shortcuts import redirect
        obj = StoreInfo.load()
        return redirect("admin:shop_storeinfo_change", obj.pk)


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ("label", "group", "short_text")
    list_filter = ("group",)
    search_fields = ("label", "text")
    ordering = ("group", "id")
    fields = ("group", "label", "key", "text")
    readonly_fields = ("group", "label", "key")

    @admin.display(description="Text")
    def short_text(self, obj):
        return obj.text if len(obj.text) < 90 else obj.text[:87] + "..."

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(group="About")        # edited in the About page

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
