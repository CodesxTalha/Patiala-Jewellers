from django.contrib.admin import AdminSite
from django.urls import reverse

from shop.models import Enquiry

from . import stats

# model -> (group, label, icon). Anything not listed goes under "More".
NAV = [
    ("Content", [
        ("view:hero", "Hero", "slides"),
        ("view:home_sections", "Home page", "home"),
        ("view:products", "Products", "gem"),
        ("view:categories", "Categories", "grid"),
        ("view:services", "Services", "wand"),
        ("view:about", "About", "star"),
        ("view:pagetext", "Page text", "text"),
    ]),
    ("Inbox", [
        ("view:enquiries", "Enquiries", "mail"),
    ]),
    ("Insights", [
        ("Visit", "Visitors", "users"),
        ("ClickEvent", "Clicks", "pointer"),
    ]),
    ("Store", [
        ("view:locations", "Locations", "pin"),
        ("view:settings", "Settings", "cog"),
    ]),
    ("Team", [
        ("User", "Users", "user"),
        ("Group", "Groups", "shield"),
    ]),
]


class PanelAdminSite(AdminSite):
    site_header = "Patiala Jewelers"
    site_title = "Patiala Jewelers Admin"
    index_title = "Overview"
    enable_nav_sidebar = False        # the panel draws its own sidebar
    index_template = "admin/panel_index.html"
    login_template = "admin/panel_login.html"

    def each_context(self, request):
        ctx = super().each_context(request)
        if not request.user.is_authenticated:
            return ctx
        found = {}
        for app in ctx["available_apps"]:
            for m in app["models"]:
                found[m["object_name"]] = m
        path = request.path
        groups = []
        for title, rows in NAV:
            items = []
            for obj_name, label, icon in rows:
                if obj_name.startswith("view:"):          # a page of the panel's own, not a model list
                    url = reverse("admin:" + obj_name[5:])
                else:
                    m = found.pop(obj_name, None)
                    if not m or not m.get("admin_url"):
                        continue
                    url = m["admin_url"]
                items.append({"label": label, "url": url, "icon": icon, "active": path.startswith(url)})
            if items:
                groups.append({"title": title, "items": items})
        extra = [{"label": m["name"], "url": m["admin_url"], "icon": "dot", "active": path.startswith(m["admin_url"])}
                 for m in found.values() if m.get("admin_url")]
        if extra:
            groups.append({"title": "More", "items": extra})
        ctx["panel_nav"] = groups
        ctx["panel_dashboard_active"] = path == reverse("admin:index")
        ctx["panel_new_enquiries"] = Enquiry.objects.filter(status="new").count()
        return ctx

    def get_urls(self):
        from django.urls import path
        from . import about, categories, enquiries, hero, home, locations, pagetext, products, services, settings
        wrap = self.admin_view
        return [
            path("hero/", wrap(lambda r: hero.editor(r, self)), name="hero"),
            path("hero/add/", wrap(hero.add_slide), name="hero_add"),
            path("hero/order/", wrap(hero.reorder), name="hero_order"),
            path("hero/settings/", wrap(hero.save_settings), name="hero_settings"),
            path("hero/<int:pk>/save/", wrap(hero.save_slide), name="hero_save"),
            path("hero/<int:pk>/delete/", wrap(hero.delete_slide), name="hero_delete"),
            path("enquiries/", wrap(lambda r: enquiries.listing(r, self)), name="enquiries"),
            path("enquiries/<int:pk>/", wrap(lambda r, pk: enquiries.detail(r, self, pk)), name="enquiry"),
            path("enquiries/<int:pk>/delete/", wrap(enquiries.delete), name="enquiry_delete"),
            path("settings/", wrap(lambda r: settings.editor(r, self)), name="settings"),
            path("text/", wrap(lambda r: pagetext.editor(r, self)), name="pagetext"),
            path("about/", wrap(lambda r: about.editor(r, self)), name="about"),
            path("home/", wrap(lambda r: home.listing(r, self)), name="home_sections"),
            path("home/sections/new/", wrap(lambda r: home.section_editor(r, self)), name="home_section_new"),
            path("home/sections/order/", wrap(home.section_order), name="home_section_order"),
            path("home/sections/<int:pk>/", wrap(lambda r, pk: home.section_editor(r, self, pk)), name="home_section_edit"),
            path("home/sections/<int:pk>/delete/", wrap(home.section_delete), name="home_section_delete"),
            path("home/sections/<int:pk>/toggle/", wrap(home.section_toggle), name="home_section_toggle"),
            path("products/", wrap(lambda r: products.listing(r, self)), name="products"),
            path("products/new/", wrap(lambda r: products.editor(r, self)), name="product_new"),
            path("products/<int:pk>/", wrap(lambda r, pk: products.editor(r, self, pk)), name="product_edit"),
            path("products/<int:pk>/delete/", wrap(products.delete), name="product_delete"),
            path("products/<int:pk>/toggle/", wrap(products.toggle), name="product_toggle"),
            path("services/", wrap(lambda r: services.listing(r, self)), name="services"),
            path("services/new/", wrap(lambda r: services.editor(r, self)), name="service_new"),
            path("services/order/", wrap(services.reorder), name="service_order"),
            path("services/<int:pk>/", wrap(lambda r, pk: services.editor(r, self, pk)), name="service_edit"),
            path("services/<int:pk>/delete/", wrap(services.delete), name="service_delete"),
            path("services/<int:pk>/toggle/", wrap(services.toggle), name="service_toggle"),
            path("locations/", wrap(lambda r: locations.listing(r, self)), name="locations"),
            path("locations/new/", wrap(lambda r: locations.editor(r, self)), name="location_new"),
            path("locations/order/", wrap(locations.reorder), name="location_order"),
            path("locations/<int:pk>/", wrap(lambda r, pk: locations.editor(r, self, pk)), name="location_edit"),
            path("locations/<int:pk>/delete/", wrap(locations.delete), name="location_delete"),
            path("locations/<int:pk>/toggle/", wrap(locations.toggle), name="location_toggle"),
            path("categories/", wrap(lambda r: categories.listing(r, self)), name="categories"),
            path("categories/new/", wrap(lambda r: categories.editor(r, self)), name="category_new"),
            path("categories/order/", wrap(categories.reorder), name="category_order"),
            path("categories/<int:pk>/", wrap(lambda r, pk: categories.editor(r, self, pk)), name="category_edit"),
            path("categories/<int:pk>/delete/", wrap(categories.delete), name="category_delete"),
            path("categories/<int:pk>/toggle/", wrap(categories.toggle), name="category_toggle"),
        ] + super().get_urls()

    def index(self, request, extra_context=None):
        try:
            days = int(request.GET.get("days", 30))
        except ValueError:
            days = 30
        days = days if days in (7, 30, 90) else 30
        context = dict(stats.overview(days), setup=stats.setup_checklist())
        context.update(extra_context or {})
        return super().index(request, context)
