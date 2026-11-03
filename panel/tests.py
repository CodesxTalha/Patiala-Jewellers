import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from shop.models import Branch, Category, ContentBlock, HeroSlide, HomeSection, Product, Service, StoreInfo

from .models import ClickEvent, Visit

# 1x1 transparent GIF
GIF = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00"
       b"\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")


@override_settings(MEDIA_ROOT="/tmp/pj-test-media")
class PanelTests(TestCase):
    def _slide(self, **kw):
        kw.setdefault("name", "Slide")
        return HeroSlide.objects.create(image=SimpleUploadedFile("s.gif", GIF, content_type="image/gif"), **kw)

    def test_page_views_and_clicks_are_counted(self):
        ua = {"HTTP_USER_AGENT": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4) Safari/604.1"}
        self.client.get(reverse("shop:home"), **ua)
        self.client.get(reverse("shop:services"), **ua)
        self.assertEqual(Visit.objects.count(), 2)
        self.assertEqual(Visit.objects.first().device, "mobile")
        self.assertEqual(Visit.objects.values("visitor").distinct().count(), 1)     # same browser, same id
        self.client.get(reverse("shop:home"), HTTP_USER_AGENT="Googlebot/2.1")
        self.client.get("/admin/login/", **ua)
        self.assertEqual(Visit.objects.count(), 2)                                  # bots and admin pages are ignored
        r = self.client.post(reverse("track_click"), data='{"kind":"whatsapp","label":"Floating button","target":"https://wa.me/1","path":"/"}',
                             content_type="application/json", **ua)
        self.assertEqual(r.status_code, 204)
        self.assertEqual(ClickEvent.objects.get().kind, "whatsapp")
        bad = self.client.post(reverse("track_click"), data='{"kind":"nonsense"}', content_type="application/json", **ua)
        self.assertEqual(bad.status_code, 400)

    def test_admin_panel_pages_open(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_superuser("owner", "o@example.com", "pw-for-tests-1")
        self.client.force_login(user)
        Visit.objects.create(visitor="a" * 32, path="/", device="mobile", browser="Chrome", ip="127.0.0.1")
        ClickEvent.objects.create(visitor="a" * 32, kind="whatsapp", label="Floating button", path="/")
        self._slide(name="Spring")
        dash = self.client.get("/admin/")
        self.assertContains(dash, "Overview")
        self.assertContains(dash, "Latest visits")
        self.assertContains(dash, "1 on the site right now")
        self.assertContains(self.client.get("/admin/?days=7"), "Last 7 days")
        for app, name in (("shop", "enquiry"), ("panel", "visit"),
                          ("panel", "clickevent")):
            self.assertEqual(self.client.get(f"/admin/{app}/{name}/").status_code, 200, name)
        for page, text in (("settings", "Colours"), ("text", "Page text")):
            self.assertContains(self.client.get(f"/admin/{page}/"), text)
        self.assertContains(self.client.get("/admin/hero/"), "Add slide")
        self.client.logout()
        self.assertEqual(self.client.get("/admin/").status_code, 302)               # signed-out visitors are sent to the login page
        self.assertContains(self.client.get("/admin/login/"), "Sign in")

    def _owner(self):
        self.client.force_login(get_user_model().objects.create_superuser("owner", "o@example.com", "pw-for-tests-1"))

    def _gif(self, name="Eid Sale.gif"):
        return SimpleUploadedFile(name, GIF, content_type="image/gif")

    def test_hero_editor_adds_edits_orders_and_deletes_slides(self):
        self._owner()
        r = self.client.post("/admin/hero/add/", {"desktop": self._gif()}).json()
        self.assertTrue(r["ok"])
        first = r["slide"]
        self.assertEqual(first["name"], "Eid Sale")
        self.assertEqual(first["kind"], "image")
        second = self.client.post("/admin/hero/add/", {"desktop": self._gif("b.gif")}).json()["slide"]
        self.assertGreater(HeroSlide.objects.get(pk=second["id"]).display_order, HeroSlide.objects.get(pk=first["id"]).display_order)

        save = f"/admin/hero/{first['id']}/save/"
        r = self.client.post(save, {"heading": " Eid is here ", "show_text": "", "text_align": "center", "seconds": "9"}).json()
        slide = HeroSlide.objects.get(pk=first["id"])
        self.assertTrue(r["ok"])
        self.assertEqual((slide.heading, slide.show_text, slide.text_align, slide.seconds), ("Eid is here", False, "center", 9))
        self.assertEqual(slide.name, "Eid Sale")                                     # fields not posted stay as they were

        bad = self.client.post(save, {"button_label": "Shop"}).json()
        self.assertFalse(bad["ok"])
        self.assertIn("A button needs a link", bad["errors"]["link"])
        self.assertEqual(HeroSlide.objects.get(pk=first["id"]).button_label, "")      # nothing half-saved
        self.assertFalse(self.client.post(save, {"link": "shop"}).json()["ok"])
        self.assertFalse(self.client.post(save, {"seconds": "2"}).json()["ok"])
        self.assertFalse(self.client.post(save, {"seconds": "abc"}).json()["ok"])

        phone = self.client.post(save, {"phone": self._gif("tall.gif")}).json()
        self.assertTrue(phone["slide"]["image_mobile"])
        self.assertTrue(self.client.post(save, {"clear_phone": "1"}).json()["ok"])
        self.assertEqual(HeroSlide.objects.get(pk=first["id"]).image_mobile.name, "")
        notpic = self.client.post(save, {"desktop": SimpleUploadedFile("x.gif", b"not a picture", content_type="image/gif")}).json()
        self.assertFalse(notpic["ok"])

        order = self.client.post("/admin/hero/order/", data=f'{{"ids":[{second["id"]},{first["id"]}]}}', content_type="application/json")
        self.assertEqual(order.status_code, 200)
        self.assertEqual([s.pk for s in HeroSlide.objects.all()], [second["id"], first["id"]])

        self.assertTrue(self.client.post(f"/admin/hero/{first['id']}/delete/").json()["ok"])
        self.assertEqual(HeroSlide.objects.count(), 1)

    def test_hero_video_slide_and_settings(self):
        self._owner()
        mp4 = SimpleUploadedFile("film.mp4", b"\x00\x00\x00\x18ftypmp42" + b"0" * 64, content_type="video/mp4")
        slide = self.client.post("/admin/hero/add/", {"desktop": mp4}).json()["slide"]
        self.assertEqual(slide["kind"], "video")
        self.assertTrue(slide["video"])
        bad = self.client.post("/admin/hero/settings/", {"hero_interval": "40"}).json()
        self.assertFalse(bad["ok"])
        ok = self.client.post("/admin/hero/settings/", {"hero_interval": "8", "hero_transition": "fade", "hero_show_dots": ""}).json()
        self.assertEqual((ok["settings"]["hero_interval"], ok["settings"]["hero_transition"], ok["settings"]["hero_show_dots"]), (8, "fade", False))

    def test_hero_editor_is_for_staff_only(self):
        self.assertEqual(self.client.get("/admin/hero/").status_code, 302)
        self.assertEqual(self.client.post("/admin/hero/add/", {"desktop": self._gif()}).status_code, 302)
        self.assertEqual(HeroSlide.objects.count(), 0)

    def _piece(self, name="Solitaire ring", **kw):
        cat = kw.pop("category", None) or Category.objects.get_or_create(name="Rings")[0]
        return Product.objects.create(name=name, category=cat, **kw)

    def test_products_list_searches_filters_and_pages(self):
        self._owner()
        rings, chains = Category.objects.create(name="Rings"), Category.objects.create(name="Chains")
        self._piece("Emerald ring", category=rings, gemstone="Emerald")
        self._piece("Gold chain", category=chains, is_active=False)
        page = self.client.get("/admin/products/")
        self.assertContains(page, "2 pieces")
        self.assertContains(page, "Emerald ring")
        self.assertContains(self.client.get("/admin/products/?q=emerald"), "Emerald ring")
        self.assertNotContains(self.client.get("/admin/products/?q=emerald"), "Gold chain")
        self.assertNotContains(self.client.get(f"/admin/products/?category={chains.pk}"), "Emerald ring")
        hidden = self.client.get("/admin/products/?status=hidden")
        self.assertContains(hidden, "Gold chain")
        self.assertNotContains(hidden, "Emerald ring")
        self.assertContains(self.client.get("/admin/products/?q=zzz"), "No pieces match")
        for i in range(30):
            self._piece(f"Piece {i}", category=rings)
        self.assertContains(self.client.get("/admin/products/"), "Page 1 of 2")
        self.assertEqual(self.client.get("/admin/products/?page=2").status_code, 200)

    def test_product_is_created_and_edited_with_photos(self):
        self._owner()
        cat = Category.objects.create(name="Rings")
        self.assertEqual(self.client.get("/admin/products/new/").status_code, 200)
        bad = self.client.post("/admin/products/new/", {"name": "", "category": "", "metal": "gold"})
        self.assertContains(bad, "Give the piece a name.")
        self.assertContains(bad, "Choose a category.")
        self.assertEqual(Product.objects.count(), 0)
        r = self.client.post("/admin/products/new/", {
            "name": "Diamond ring", "category": cat.pk, "metal": "white_gold", "purity": "18K", "price": "185000",
            "weight_grams": "4.5", "is_active": "on", "image": self._gif("main.gif"),
            "gallery": [self._gif("a.gif"), self._gif("b.gif")],
        })
        piece = Product.objects.get()
        self.assertRedirects(r, f"/admin/products/{piece.pk}/")
        self.assertEqual((piece.slug, piece.price_label, piece.is_featured), ("diamond-ring", "Rs 185,000", False))
        self.assertTrue(piece.image)
        self.assertEqual(piece.gallery.count(), 2)

        keep, drop = list(piece.gallery.all())
        r = self.client.post(f"/admin/products/{piece.pk}/", {
            "name": "Diamond ring II", "category": cat.pk, "metal": "gold", "price": "", "is_active": "on", "is_featured": "on",
            "remove_gallery": [drop.pk], "gallery": [self._gif("c.gif")],
        })
        self.assertEqual(r.status_code, 302)
        piece.refresh_from_db()
        self.assertEqual((piece.name, piece.slug, piece.price_label, piece.is_featured), ("Diamond ring II", "diamond-ring", "Price on request", True))
        self.assertTrue(piece.image)                                            # the photo stays unless you remove it
        self.assertEqual(piece.gallery.count(), 2)
        self.assertTrue(piece.gallery.filter(pk=keep.pk).exists())
        self.assertFalse(piece.gallery.filter(pk=drop.pk).exists())

        self.client.post(f"/admin/products/{piece.pk}/", {"name": "Diamond ring II", "category": cat.pk, "metal": "gold", "is_active": "on", "clear_image": "1"})
        piece.refresh_from_db()
        self.assertFalse(piece.image)
        notpic = self.client.post(f"/admin/products/{piece.pk}/", {"name": "x", "category": cat.pk, "metal": "gold",
                                  "gallery": [SimpleUploadedFile("x.gif", b"nope", content_type="image/gif")]})
        self.assertContains(notpic, "Please check the highlighted fields.")
        piece.refresh_from_db()
        self.assertEqual(piece.name, "Diamond ring II")                         # a failed save changes nothing

    def test_product_toggle_and_delete(self):
        self._owner()
        piece = self._piece()
        r = self.client.post(f"/admin/products/{piece.pk}/toggle/", {"field": "is_active"}).json()
        self.assertEqual((r["ok"], r["value"]), (True, False))
        self.assertTrue(self.client.post(f"/admin/products/{piece.pk}/toggle/", {"field": "is_featured"}).json()["value"])
        self.assertEqual(self.client.post(f"/admin/products/{piece.pk}/toggle/", {"field": "price"}).status_code, 400)
        piece.refresh_from_db()
        self.assertEqual((piece.is_active, piece.is_featured), (False, True))
        self.assertRedirects(self.client.post(f"/admin/products/{piece.pk}/delete/"), "/admin/products/")
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(self.client.get("/admin/products/999/").status_code, 404)

    def test_products_are_for_staff_only(self):
        piece = self._piece()
        for url in ("/admin/products/", "/admin/products/new/", f"/admin/products/{piece.pk}/"):
            self.assertEqual(self.client.get(url).status_code, 302, url)
        self.assertEqual(self.client.post(f"/admin/products/{piece.pk}/delete/").status_code, 302)
        self.assertEqual(Product.objects.count(), 1)

    def test_categories_are_listed_ordered_created_edited_and_deleted(self):
        self._owner()
        rings = Category.objects.create(name="Rings", display_order=0)
        chains = Category.objects.create(name="Chains", display_order=1)
        self._piece("Emerald ring", category=rings)
        page = self.client.get("/admin/categories/")
        self.assertContains(page, "Rings")
        self.assertContains(page, "1 piece<")
        self.assertContains(page, "0 pieces")

        r = self.client.post("/admin/categories/new/", {"name": "Bangles", "description": "Gold bangles", "is_active": "on", "image": self._gif("b.gif")})
        bangles = Category.objects.get(name="Bangles")
        self.assertRedirects(r, f"/admin/categories/{bangles.pk}/")
        self.assertEqual((bangles.slug, bangles.display_order), ("bangles", 2))      # new ones go last
        self.assertTrue(bangles.image)
        self.assertContains(self.client.post("/admin/categories/new/", {"name": ""}), "Give the category a name.")
        self.assertContains(self.client.post("/admin/categories/new/", {"name": "Rings"}), "already a category")

        self.client.post(f"/admin/categories/{bangles.pk}/", {"name": "Gold bangles", "clear_image": "1"})
        bangles.refresh_from_db()
        self.assertEqual((bangles.name, bool(bangles.image), bangles.is_active, bangles.slug), ("Gold bangles", False, False, "bangles"))
        self.assertTrue(self.client.post(f"/admin/categories/{bangles.pk}/toggle/").json()["value"])

        order = self.client.post("/admin/categories/order/", data=f'{{"ids":[{bangles.pk},{chains.pk},{rings.pk}]}}', content_type="application/json")
        self.assertEqual(order.status_code, 200)
        self.assertEqual([c.name for c in Category.objects.all()], ["Gold bangles", "Chains", "Rings"])

        self.client.post(f"/admin/categories/{rings.pk}/delete/")                    # has a piece: refused
        self.assertTrue(Category.objects.filter(pk=rings.pk).exists())
        self.assertContains(self.client.get(f"/admin/categories/{rings.pk}/"), "first move or delete")
        self.assertRedirects(self.client.post(f"/admin/categories/{chains.pk}/delete/"), "/admin/categories/")
        self.assertFalse(Category.objects.filter(pk=chains.pk).exists())

    def test_categories_are_for_staff_only(self):
        cat = Category.objects.create(name="Rings")
        self.assertEqual(self.client.get("/admin/categories/").status_code, 302)
        self.assertEqual(self.client.post(f"/admin/categories/{cat.pk}/delete/").status_code, 302)
        self.assertTrue(Category.objects.filter(pk=cat.pk).exists())

    def test_services_are_listed_created_edited_ordered_and_deleted(self):
        self._owner()
        a = Service.objects.create(name="Polishing", summary="Shine again.", display_order=0)
        b = Service.objects.create(name="Repair", summary="Fixed by hand.", display_order=1)
        page = self.client.get("/admin/services/")
        self.assertContains(page, "Polishing")
        self.assertContains(page, "Fixed by hand.")
        self.assertContains(self.client.get("/admin/services/new/"), "What is included")

        bad = self.client.post("/admin/services/new/", {"name": "", "summary": ""})
        self.assertContains(bad, "Give the service a name.")
        self.assertContains(bad, "Add one short line.")
        self.assertContains(self.client.post("/admin/services/new/", {"name": "Polishing", "summary": "x"}), "already a service")

        r = self.client.post("/admin/services/new/", {
            "name": "Ring resizing", "summary": "Fits perfectly.", "intro": "Sized up or down.", "description": "Details.",
            "includes": "Measuring\nResizing", "process": "Bring it in | We measure.\nCollect it | Often same day.",
            "turnaround": "Same day", "price_note": "From Rs 1,500", "is_active": "on", "image": self._gif("s.gif"),
        })
        s = Service.objects.get(name="Ring resizing")
        self.assertRedirects(r, f"/admin/services/{s.pk}/")
        self.assertEqual((s.slug, s.display_order, s.include_list), ("ring-resizing", 2, ["Measuring", "Resizing"]))
        self.assertEqual(s.step_list[1], {"title": "Collect it", "text": "Often same day."})
        self.assertTrue(s.image)
        edit = self.client.get(f"/admin/services/{s.pk}/")
        self.assertContains(edit, "Bring it in")                                       # the lists are filled from the saved text
        self.client.post(f"/admin/services/{s.pk}/", {"name": "Ring resizing", "summary": "Fits perfectly.", "clear_image": "1"})
        s.refresh_from_db()
        self.assertEqual((bool(s.image), s.is_active, s.slug, s.includes), (False, False, "ring-resizing", ""))
        self.assertTrue(self.client.post(f"/admin/services/{s.pk}/toggle/").json()["value"])

        order = self.client.post("/admin/services/order/", data=f'{{"ids":[{s.pk},{b.pk},{a.pk}]}}', content_type="application/json")
        self.assertEqual(order.status_code, 200)
        self.assertEqual([x.name for x in Service.objects.all()], ["Ring resizing", "Repair", "Polishing"])
        self.assertRedirects(self.client.post(f"/admin/services/{b.pk}/delete/"), "/admin/services/")
        self.assertEqual(Service.objects.count(), 2)

    def test_services_are_for_staff_only(self):
        s = Service.objects.create(name="Polishing", summary="Shine.")
        self.assertEqual(self.client.get("/admin/services/").status_code, 302)
        self.assertEqual(self.client.post(f"/admin/services/{s.pk}/delete/").status_code, 302)
        self.assertEqual(Service.objects.count(), 1)

    def test_locations_are_listed_created_edited_ordered_and_deleted(self):
        self._owner()
        Branch.objects.all().delete()
        a = Branch.objects.create(name="Gulberg", display_order=0, latitude="33.6", longitude="73.15")
        b = Branch.objects.create(name="DHA", display_order=1)
        page = self.client.get("/admin/locations/")
        self.assertContains(page, "Gulberg")
        self.assertContains(page, "no map pin")
        self.assertContains(self.client.get("/admin/locations/new/"), "Map pin")

        self.assertContains(self.client.post("/admin/locations/new/", {"name": "", "city": "Islamabad"}), "Give the location a name.")
        self.assertContains(self.client.post("/admin/locations/new/", {"name": "F7", "latitude": "33.7"}), "Set both numbers")
        self.assertContains(self.client.post("/admin/locations/new/", {"name": "F7", "latitude": "133.7", "longitude": "73"}), "between -90 and 90")
        r = self.client.post("/admin/locations/new/", {"name": "F7", "city": "Islamabad", "address": "Shop 1", "latitude": "33.720000",
                                                       "longitude": "73.056000", "is_active": "on"})
        f7 = Branch.objects.get(name="F7")
        self.assertRedirects(r, f"/admin/locations/{f7.pk}/")
        self.assertEqual((f7.display_order, float(f7.latitude), f7.is_active), (2, 33.72, True))
        self.client.post(f"/admin/locations/{f7.pk}/", {"name": "F7 Markaz", "city": "Islamabad"})
        f7.refresh_from_db()
        self.assertEqual((f7.name, f7.latitude, f7.is_active), ("F7 Markaz", None, False))        # clearing both numbers removes the pin
        self.assertTrue(self.client.post(f"/admin/locations/{f7.pk}/toggle/").json()["value"])
        self.client.post("/admin/locations/order/", data=f'{{"ids":[{f7.pk},{b.pk},{a.pk}]}}', content_type="application/json")
        self.assertEqual([x.name for x in Branch.objects.all()], ["F7 Markaz", "DHA", "Gulberg"])
        self.assertRedirects(self.client.post(f"/admin/locations/{b.pk}/delete/"), "/admin/locations/")
        self.assertEqual(Branch.objects.count(), 2)

    def test_home_starts_with_the_old_sections_as_an_orderable_list(self):
        self._owner()
        kinds = list(HomeSection.objects.values_list("kind", flat=True))
        self.assertEqual(kinds, ["collections", "products", "services", "story", "locations"])      # what the page had before
        page = self.client.get("/admin/home/")
        for text in ("Find your piece", "Made to be worn", "Care for every piece", "Cast in gold", "Open Hero", "Add section"):
            self.assertContains(page, text)
        ids = list(HomeSection.objects.values_list("pk", flat=True))
        r = self.client.post("/admin/home/sections/order/", data=json.dumps({"ids": ids[::-1]}), content_type="application/json")
        self.assertEqual(r.json(), {"ok": True})
        self.assertEqual(list(HomeSection.objects.values_list("pk", flat=True)), ids[::-1])
        self.assertContains(self.client.get("/admin/home/sections/new/"), "What do you want to add?")

    def test_home_page_follows_the_saved_order_and_switches(self):
        self._owner()
        Category.objects.create(name="Rings")
        Service.objects.create(name="Resizing", summary="Sized to fit.")
        home = self.client.get("/").content.decode()
        order = [home.index(t) for t in ("Find your piece", "Care for every piece", "Cast in gold")]
        self.assertEqual(order, sorted(order))
        story, services = HomeSection.objects.get(kind="story"), HomeSection.objects.get(kind="services")
        self.client.post("/admin/home/sections/order/", data=json.dumps({"ids": [story.pk, services.pk]}), content_type="application/json")
        home = self.client.get("/").content.decode()
        self.assertLess(home.index("Cast in gold"), home.index("Care for every piece"))
        self.assertTrue(self.client.post(f"/admin/home/sections/{story.pk}/toggle/").json()["ok"])
        self.assertNotContains(self.client.get("/"), "Cast in gold")

    def test_image_and_text_section_with_a_photo_beside_the_words_or_behind_them(self):
        self._owner()
        r = self.client.post("/admin/home/sections/new/", {"kind": "story", "title": "Eid offer", "label": "This week", "text": "Free <b>engraving</b>.",
                                                           "button_label": "Visit", "link": "/contact/", "layout": "right", "theme": "dark",
                                                           "is_active": "on", "count": "4", "cols": "4", "cols_mobile": "2", "image": self._gif("offer.gif")})
        sec = HomeSection.objects.get(title="Eid offer")
        self.assertRedirects(r, f"/admin/home/sections/{sec.pk}/")
        self.assertTrue(sec.image)
        home = self.client.get("/")
        self.assertContains(home, "imgtext is-right")
        self.assertContains(home, sec.image.url)
        self.assertContains(home, 'href="/contact/"')
        self.client.post(f"/admin/home/sections/{sec.pk}/", {"kind": "story", "title": "Eid offer", "layout": "behind", "is_active": "on", "count": "4",
                                                              "cols": "4", "cols_mobile": "2", "theme": "light", "clear_image": "1"})
        sec.refresh_from_db()
        self.assertEqual((sec.layout, bool(sec.image)), ("behind", False))
        self.assertContains(self.client.get("/"), 'class="story surface-dark"')
        bad = self.client.post("/admin/home/sections/new/", {"kind": "story", "title": "X", "count": "4", "cols": "4", "cols_mobile": "2", "theme": "light",
                                                               "image": SimpleUploadedFile("x.gif", b"nope", content_type="image/gif")})
        self.assertContains(bad, "Please check the highlighted fields.")

    def test_contact_section_shows_phone_whatsapp_and_email_from_store_settings(self):
        self._owner()
        info = StoreInfo.load()
        info.phone, info.whatsapp, info.email = "+92 51 1234567", "923001234567", "hello@example.com"
        info.instagram_url, info.facebook_url = "https://instagram.com/patiala", "https://facebook.com/patiala"
        info.save()
        self.client.post("/admin/home/sections/new/", {"kind": "contact", "title": "Talk to us", "count": "4", "cols": "4", "cols_mobile": "2",
                                                       "theme": "light", "is_active": "on"})
        home = self.client.get("/")
        self.assertContains(home, "Talk to us")
        for text in ("tel:+92 51 1234567", "https://wa.me/923001234567", "mailto:hello@example.com"):
            self.assertContains(home, text)
        for text in ('aria-label="Instagram"', 'aria-label="Facebook"'):                 # social links are icons, not "Follow us" rows
            self.assertContains(home, text)
        self.assertNotContains(home, "Follow us")
        self.assertNotContains(self.client.get("/contact/"), "Follow us")
        self.assertContains(self.client.get("/contact/"), 'class="social-btn"')

    def test_products_section_uses_a_collections_link_or_the_featured_pieces(self):
        self._owner()
        rings = Category.objects.create(name="Rings")
        chains = Category.objects.create(name="Chains")
        Product.objects.create(name="Gold band", category=rings, metal="gold")
        Product.objects.create(name="Silver band", category=rings, metal="silver")
        Product.objects.create(name="Gold chain", category=chains, metal="gold", is_featured=True)
        HomeSection.objects.all().delete()
        base = {"kind": "products", "title": "Gold rings", "count": "4", "theme": "dark", "cols": "3", "cols_mobile": "1",
                "is_active": "on", "button_label": "See all rings"}
        r = self.client.post("/admin/home/sections/new/", dict(base, link="http://localhost:8000/collections/?category=rings&metal=gold"))
        sec = HomeSection.objects.get()
        self.assertRedirects(r, f"/admin/home/sections/{sec.pk}/")
        self.assertEqual(sec.link, "/collections/?category=rings&metal=gold")             # the host is dropped
        home = self.client.get("/")
        self.assertContains(home, "Gold band")
        self.assertNotContains(home, "Silver band")                                       # filtered by the link
        self.assertNotContains(home, "Gold chain")
        self.assertContains(home, "surface-dark")
        self.assertContains(home, "grid-set d3 m1")
        self.assertContains(home, 'href="/collections/?category=rings&amp;metal=gold"')

        for link, text in (("https://example.com/shop", "link to your Collections page"),
                           ("/collections/?category=nope", "no category called"), ("/collections/?metal=wood", "not one we have")):
            self.assertContains(self.client.post("/admin/home/sections/new/", dict(base, link=link)), text)
        self.assertEqual(HomeSection.objects.count(), 1)

        self.client.post(f"/admin/home/sections/{sec.pk}/", dict(base, link=""))            # no link: the featured pieces
        home = self.client.get("/")
        self.assertContains(home, "Gold chain")
        self.assertNotContains(home, "Gold band")

        self.client.post(f"/admin/home/sections/{sec.pk}/delete/")
        self.assertFalse(HomeSection.objects.filter(pk=sec.pk).exists())

    def test_settings_and_page_text_are_single_pages(self):
        self._owner()
        page = self.client.get("/admin/settings/")
        for text in ("Brand", "Contact", "Social media", "Colours", "Fonts", "On every page", "Save changes"):
            self.assertContains(page, text)
        data = {"name": "Patiala Jewelers", "descriptor": "Gold", "tagline": "Hello", "phone": "0300", "whatsapp": "+92 300 1234567",
                "email": "a@b.co", "instagram_url": "https://instagram.com/x", "color_light": "#FFFFFF", "color_dark": "#111111",
                "color_gold": "#B8975A", "color_gold_light": "#C9A96A", "color_gold_deep": "#8A6D35", "color_cream": "#F3EFE6",
                "font_primary": "Montserrat", "heading_weight": "500", "font_secondary": "Playfair Display",
                "font_wordmark": "Playfair Display", "whatsapp_message": "Hi there", "show_whatsapp_button": "on"}
        self.assertRedirects(self.client.post("/admin/settings/", data), "/admin/settings/")
        store = StoreInfo.load()
        self.assertEqual((store.whatsapp, store.color_light, store.show_preloader, store.show_whatsapp_button), ("923001234567", "#FFFFFF", False, True))
        self.assertContains(self.client.post("/admin/settings/", dict(data, color_light="red", name="")), "Please check")
        self.assertEqual(StoreInfo.load().color_light, "#FFFFFF")
        text = self.client.get("/admin/text/")
        self.assertContains(text, "Services")
        for gone in ("WhatsApp button text", "Hero:", "Service page: steps", "Closing line"):
            self.assertNotContains(text, gone)
        self.assertEqual(text.content.decode().count('name="t_services_'), 3)
        self.client.post("/admin/text/", {"t_collections_title": "Every piece"})
        self.assertContains(self.client.get("/collections/"), "Every piece")

    def test_about_is_one_page_for_everything_on_the_about_page(self):
        from shop.models import AboutValue
        self._owner()
        AboutValue.objects.all().delete()
        page = self.client.get("/admin/about/")
        for text in ("Top of the page", "Your story", "Promises", "Closing line", "Save changes"):
            self.assertContains(page, text)
        a = AboutValue.objects.create(title="Old promise", text="Stays.")
        b = AboutValue.objects.create(title="Gone promise", text="Removed.")
        promises = [{"id": a.pk, "title": "Made in Islamabad", "text": "Every piece.", "on": True},
                    {"id": None, "title": "New one", "text": "Fresh.", "on": False},
                    {"id": None, "title": "", "text": "", "on": True}]                       # an empty row is ignored
        r = self.client.post("/admin/about/", {"about_label": "Who we are", "about_heading": "Our <i>Story</i>", "about_text": "First.\n\nSecond.",
                                               "about_button": "Visit us", "about_quote": "Made to last.", "about_quote_button": "",
                                               "promises": json.dumps(promises), "about_image": self._gif("about.gif"),
                                               "show_about_story": "on", "show_about_promises": "on", "show_about_closing": "on"})
        self.assertRedirects(r, "/admin/about/")
        store = StoreInfo.load()
        self.assertEqual((store.about_heading, store.about_text), ("Our Story", "First.\n\nSecond."))
        self.assertTrue(store.about_image)
        self.assertEqual([(v.title, v.is_active) for v in AboutValue.objects.all()], [("Made in Islamabad", True), ("New one", False)])
        self.assertFalse(AboutValue.objects.filter(pk=b.pk).exists())
        about = self.client.get("/about/")
        for text in ("Who we are", "Our Story", "Second.", "Made in Islamabad", "Made to last."):
            self.assertContains(about, text)
        self.assertNotContains(about, "New one")                 # hidden promise
        self.assertNotContains(about, "Discover the collections")  # cleared button text hides the button
        self.assertNotContains(self.client.get("/admin/text/"), "Closing line")   # edited in About, not in Page text

        self.client.post("/admin/about/", {"about_heading": "Our Story", "promises": json.dumps(promises[:1])})   # all three switches off
        about = self.client.get("/about/")
        for text in ("Second.", "Made in Islamabad", "Made to last."):
            self.assertNotContains(about, text)
        self.assertContains(about, "Our Story")
        self.assertContains(self.client.get("/admin/about/"), "show_about_closing")
        self.client.post("/admin/about/", {"about_heading": "Our Story", "promises": json.dumps(promises[:1]), "show_about_closing": "on"})
        self.assertContains(self.client.get("/about/"), "Made to last.")

        for data, text in (({"about_heading": ""}, "Give the page a heading."),
                           ({"about_heading": "X", "promises": json.dumps([{"title": "", "text": "no title"}])}, "short title"),
                           ({"about_heading": "X", "about_image": SimpleUploadedFile("x.gif", b"nope", content_type="image/gif")}, "Please check")):
            self.assertContains(self.client.post("/admin/about/", data), text)
        self.client.post("/admin/about/", {"about_heading": "Our Story", "promises": "[]", "clear_image": "1"})
        self.assertFalse(StoreInfo.load().about_image)
        self.assertFalse(AboutValue.objects.exists())
        self.assertNotContains(self.client.get("/about/"), 'class="values"')

    def test_locations_and_home_sections_are_for_staff_only(self):
        for url in ("/admin/locations/", "/admin/locations/new/", "/admin/home/", "/admin/home/sections/new/", "/admin/about/"):
            self.assertEqual(self.client.get(url).status_code, 302, url)
        self.assertEqual(self.client.post("/admin/home/sections/order/", data="{}", content_type="application/json").status_code, 302)
