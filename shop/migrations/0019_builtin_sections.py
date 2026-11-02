from django.db import migrations

REMOVED_KEYS = [k for k in ("home_collections_label", "home_collections_title", "home_featured_label", "home_featured_title",
                            "home_featured_button", "home_services_label", "home_services_title", "home_story_label", "home_story_title",
                            "home_story_text", "home_story_button", "home_boutiques_label", "home_boutiques_title", "home_boutiques_button")]


# The starting words of the old fixed sections (they are no longer in shop/content.py).
OLD = {
    "home_collections_label": "The collections", "home_collections_title": "Find your piece",
    "home_featured_label": "Selected pieces", "home_featured_title": "Made to be worn", "home_featured_button": "View all pieces",
    "home_services_label": "Services", "home_services_title": "Care for every piece", "home_services_button": "All services",
    "home_story_label": "Our story", "home_story_title": "Cast in gold, finished by hand.",
    "home_story_text": "We keep our collections small, so every design gets the time it deserves. Each piece is checked twice before it leaves the workshop.",
    "home_story_button": "Read our story",
    "home_boutiques_label": "Boutiques", "home_boutiques_title": "Visit us in Islamabad", "home_boutiques_button": "View on the map",
}


def to_sections(apps, schema_editor):
    """The five fixed home sections become ordinary, orderable sections that keep their words and settings."""
    HomeSection = apps.get_model("shop", "HomeSection")
    StoreInfo = apps.get_model("shop", "StoreInfo")
    ContentBlock = apps.get_model("shop", "ContentBlock")
    info = StoreInfo.objects.first()
    texts = dict(OLD)
    texts.update(dict(ContentBlock.objects.values_list("key", "text")))

    def flag(name):
        return getattr(info, name) if info else True

    def pick(name, default):
        return getattr(info, name) if info else default

    builtin = {
        "collections": dict(kind="collections", label=texts["home_collections_label"], title=texts["home_collections_title"],
                            count=6, is_active=flag("show_collections")),
        "featured": dict(kind="products", label=texts["home_featured_label"], title=texts["home_featured_title"],
                         button_label=texts["home_featured_button"], count=8, cols=pick("featured_cols", 4),
                         cols_mobile=pick("featured_cols_mobile", 2), theme=pick("featured_theme", "light"), is_active=flag("show_featured")),
        "services": dict(kind="services", label=texts["home_services_label"], title=texts["home_services_title"],
                         button_label=texts["home_services_button"], link="/services/", count=4, cols=pick("services_cols", 3),
                         cols_mobile=pick("services_cols_mobile", 1), theme=pick("services_theme", "light"), is_active=flag("show_services")),
        "story": dict(kind="story", label=texts["home_story_label"], title=texts["home_story_title"], text=texts["home_story_text"],
                      button_label=texts["home_story_button"], link="/about/", layout="left", is_active=flag("show_story")),
        "boutiques": dict(kind="locations", label=texts["home_boutiques_label"], title=texts["home_boutiques_title"],
                          button_label=texts["home_boutiques_button"], is_active=flag("show_boutiques")),
    }
    mine = list(HomeSection.objects.order_by("display_order", "id"))        # sections made before this change
    order = 0
    for slot in ("hero", "collections", "featured", "services", "story", "boutiques"):
        for sec in [m for m in mine if m.after == slot]:
            sec.display_order = order
            sec.save(update_fields=["display_order"])
            order += 1
        if slot in builtin:
            HomeSection.objects.create(display_order=order, after=slot, **builtin[slot])
            order += 1
    ContentBlock.objects.filter(key__in=REMOVED_KEYS).delete()


class Migration(migrations.Migration):
    dependencies = [("shop", "0018_home_section_fields")]
    operations = [migrations.RunPython(to_sections, migrations.RunPython.noop)]
