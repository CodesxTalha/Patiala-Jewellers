from .models import Branch, Category, StoreInfo

# Used for the Our Story photo until one is uploaded in the admin.
STORY_IMAGE_FALLBACK = "https://images.unsplash.com/photo-1758995116383-f51775896add?w=2000&q=75&auto=format&fit=crop"


def store_info(request):
    """Make store details, categories and boutiques available on every page."""
    store = StoreInfo.load()
    story_image = store.about_image.url if store.about_image else STORY_IMAGE_FALLBACK
    return {
        "store": store,
        "nav_categories": Category.objects.filter(is_active=True),
        "branches": Branch.objects.filter(is_active=True),
        "story_image": story_image,
        # Phones use their own photo when one is uploaded, otherwise the same photo as desktop.
        "story_image_mobile": store.about_image_mobile.url if store.about_image_mobile else story_image,
    }
