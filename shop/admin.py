from django.contrib import admin
from django.utils.html import format_html

from .models import Branch, Category, Enquiry, HeroSlide, Product, ProductImage, Service, StoreInfo

admin.site.site_header = "Patiala Jewelers Admin"
admin.site.site_title = "Patiala Jewelers Admin"
admin.site.index_title = "Manage your store"


def thumb(url, size=60):
    if not url:
        return "—"
    return format_html(
        '<img src="{}" style="height:{}px;width:{}px;object-fit:cover;border-radius:6px;">',
        url, size, size,
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("preview", "name", "product_count", "display_order", "is_active")
    list_display_links = ("preview", "name")
    list_editable = ("display_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    @admin.display(description="Image")
    def preview(self, obj):
        return thumb(obj.photo_url, 40)

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "image_url", "alt_text", "display_order")
    readonly_fields = ("preview",)

    @admin.display(description="Preview")
    def preview(self, obj):
        return thumb(obj.photo_url)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("preview", "name", "category", "metal", "purity", "price_display", "is_featured", "is_active")
    list_display_links = ("preview", "name")
    list_editable = ("is_featured", "is_active")
    list_filter = ("category", "metal", "is_featured", "is_active")
    search_fields = ("name", "description", "gemstone")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("large_preview", "created_at", "updated_at")
    inlines = [ProductImageInline]
    list_per_page = 25
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "description")}),
        ("Details", {"fields": ("metal", "purity", "weight_grams", "gemstone", "price")}),
        ("Photo", {"fields": ("image", "image_url", "large_preview")}),
        ("Visibility", {"fields": ("is_featured", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Image")
    def preview(self, obj):
        return thumb(obj.photo_url, 50)

    @admin.display(description="Preview")
    def large_preview(self, obj):
        return thumb(obj.photo_url, 200)

    @admin.display(description="Price", ordering="price")
    def price_display(self, obj):
        return f"Rs {obj.price:,.0f}" if obj.price is not None else "On request"


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


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("preview", "caption", "tone", "display_order", "is_active")
    list_display_links = ("preview", "caption")
    list_editable = ("display_order", "is_active")
    readonly_fields = ("large_preview",)
    fields = ("image", "large_preview", "caption", "subtitle", "link", "tone", "focus", "display_order", "is_active")

    @admin.display(description="Image")
    def preview(self, obj):
        return thumb(obj.image.url if obj.image else "", 60)

    @admin.display(description="Preview")
    def large_preview(self, obj):
        return thumb(obj.image.url if obj.image else "", 240)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    exclude = ("map_embed_url",)
    list_display = ("name", "city", "phone", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    search_fields = ("name", "address")


@admin.register(StoreInfo)
class StoreInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Brand", {"fields": ("name", "descriptor", "tagline")}),
        ("Contact", {"fields": ("phone", "whatsapp", "email")}),
        ("Social", {"fields": ("instagram_url", "facebook_url")}),
        ("About page and Our Story section", {"fields": ("about_heading", "about_text", "about_image", "about_image_mobile")}),
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


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "summary", "turnaround", "price_note", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    search_fields = ("name", "summary")
