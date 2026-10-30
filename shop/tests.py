from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AboutValue, Category, ContentBlock, Enquiry, Product, Service, StoreInfo

# 1x1 transparent GIF
GIF = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00"
       b"\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")


@override_settings(MEDIA_ROOT="/tmp/pj-test-media")
class ShopTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Necklaces")
        self.product = Product.objects.create(
            name="Kundan Necklace", category=self.cat, is_featured=True,
            image=SimpleUploadedFile("n.gif", GIF, content_type="image/gif"),
        )

    def test_pages_load(self):
        for name in ("home", "collections", "about", "contact"):
            self.assertEqual(self.client.get(reverse(f"shop:{name}")).status_code, 200, name)
        self.assertContains(self.client.get(self.product.get_absolute_url()), "Kundan Necklace")

    def test_hidden_product_404(self):
        self.product.is_active = False
        self.product.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)

    def test_slug_unique(self):
        p2 = Product.objects.create(name="Kundan Necklace", category=self.cat, image="x.gif")
        self.assertEqual(p2.slug, "kundan-necklace-2")

    def test_category_filter(self):
        resp = self.client.get(reverse("shop:collections"), {"category": "necklaces"})
        self.assertContains(resp, "Kundan Necklace")

    def test_contact_enquiry(self):
        resp = self.client.post(reverse("shop:contact"), {
            "name": "Asha", "phone": "+91 98765 43210", "message": "Hello",
        })
        self.assertRedirects(resp, reverse("shop:contact"))
        self.assertEqual(Enquiry.objects.count(), 1)

    def test_product_enquiry_links_product(self):
        self.client.post(self.product.get_absolute_url(), {
            "name": "Asha", "phone": "9876543210", "message": "Price?",
        })
        self.assertEqual(Enquiry.objects.get().product, self.product)

    def test_honeypot_blocks_bots(self):
        self.client.post(reverse("shop:contact"), {
            "name": "Bot", "phone": "9876543210", "message": "spam", "website": "x",
        })
        self.assertEqual(Enquiry.objects.count(), 0)

    def test_store_info_singleton(self):
        StoreInfo(name="A").save()
        StoreInfo(name="B").save()
        self.assertEqual(StoreInfo.objects.count(), 1)
        self.assertEqual(StoreInfo.load().name, "B")

    def test_home_has_hero_video_for_desktop_and_phone(self):
        resp = self.client.get(reverse("shop:home"))
        for f in ("hero.webm", "hero.mp4", "hero-mobile.webm", "hero-mobile.mp4", "hero-poster.jpg", "hero-poster-mobile.jpg"):
            self.assertContains(resp, f"img/hero/{f}")

    def test_image_link_used_when_no_upload(self):
        p = Product.objects.create(
            name="Linked Ring", category=self.cat, price=125000,
            image_url="https://example.com/ring.jpg",
        )
        self.assertEqual(p.photo_url, "https://example.com/ring.jpg")
        self.assertEqual(p.price_label, "Rs 125,000")
        self.assertContains(self.client.get(reverse("shop:collections")), "https://example.com/ring.jpg")

    def test_price_on_request(self):
        self.assertEqual(self.product.price_label, "Price on request")

    def test_product_page_has_whatsapp_enquiry(self):
        StoreInfo.load()
        info = StoreInfo.load(); info.whatsapp = "923001234567"; info.save()
        resp = self.client.get(self.product.get_absolute_url())
        self.assertContains(resp, "wa.me/923001234567")
        self.assertContains(resp, "Kundan%20Necklace")

    def test_favorites_page_lists_pieces_as_json(self):
        resp = self.client.get(reverse("shop:favorites"))
        self.assertContains(resp, 'id="all-pieces"')
        self.assertContains(resp, "kundan-necklace")

    def test_favorites_page(self):
        self.assertEqual(self.client.get(reverse("shop:favorites")).status_code, 200)

    def test_story_uses_desktop_photo_on_phones_when_no_mobile_photo(self):
        resp = self.client.get(reverse("shop:home"))
        html = resp.content.decode()
        import re
        srcset = re.search(r'<source media="\(max-width: 767px\)" srcset="([^"]+)"', html).group(1)
        img = re.search(r'<picture>.*?<img src="([^"]+)"', html, re.S).group(1)
        self.assertEqual(srcset, img)

    def test_story_uses_mobile_photo_when_uploaded(self):
        info = StoreInfo.load()
        info.about_image_mobile = SimpleUploadedFile("m.gif", GIF, content_type="image/gif")
        info.save()
        html = self.client.get(reverse("shop:home")).content.decode()
        import re
        srcset = re.search(r'<source media="\(max-width: 767px\)" srcset="([^"]+)"', html).group(1)
        img = re.search(r'<picture>.*?<img src="([^"]+)"', html, re.S).group(1)
        self.assertIn("/store/m", srcset)
        self.assertNotEqual(srcset, img)

    def test_services_pages(self):
        sv = Service.objects.create(
            name="Polishing", summary="Restores the shine.", intro="Bring back the shine.", turnaround="Same day",
            includes="Hand polish\nUltrasonic clean", process="Bring it in|Visit us.\nCollect it|Often same day.",
        )
        Service.objects.create(name="Hidden", summary="Not shown.", is_active=False)
        StoreInfo(whatsapp="923001234567").save()
        self.assertEqual(sv.slug, "polishing")
        listing = self.client.get(reverse("shop:services"))
        self.assertContains(listing, "Polishing")
        self.assertNotContains(listing, "Hidden")
        self.assertContains(self.client.get(reverse("shop:home")), "Restores the shine.")
        page = self.client.get(sv.get_absolute_url())
        self.assertContains(page, "Bring back the shine.")
        self.assertContains(page, "Ultrasonic clean")
        self.assertContains(page, "Collect it")
        self.assertContains(page, "wa.me/923001234567?text=Hello")
        self.assertEqual(self.client.get(reverse("shop:service_detail", args=["hidden"])).status_code, 404)

    def test_brand_settings_drive_the_theme(self):
        info = StoreInfo.load()
        info.color_gold = "#112233"
        info.font_primary = "Jost"
        info.heading_weight = 600
        info.tiktok_url = "https://tiktok.com/@patiala"
        info.save()
        home = self.client.get(reverse("shop:home"))
        self.assertContains(home, "--gold:#112233")
        self.assertContains(home, "--heading-weight:600")
        self.assertContains(home, "family=Jost:wght@400;500;600")
        self.assertContains(home, "https://tiktok.com/@patiala")
        self.assertContains(home, 'class="monogram')       # built-in monogram when no logo is uploaded
        info.logo = SimpleUploadedFile("logo.gif", GIF, content_type="image/gif")
        info.save()
        self.assertContains(self.client.get(reverse("shop:home")), "<img class=\"monogram")

    def test_page_text_comes_from_the_database(self):
        self.assertContains(self.client.get(reverse("shop:home")), "Find your piece")
        ContentBlock.objects.filter(key="home_collections_title").update(text="Choose your treasure")
        home = self.client.get(reverse("shop:home"))
        self.assertContains(home, "Choose your treasure")
        self.assertNotContains(home, "Find your piece")
        # a missing row never breaks the page: the starting text is used
        ContentBlock.objects.filter(key="home_collections_title").delete()
        self.assertContains(self.client.get(reverse("shop:home")), "Find your piece")

    def test_about_values_come_from_the_database(self):
        AboutValue.objects.all().delete()
        AboutValue.objects.create(title="Made in Islamabad", text="Every piece.")
        AboutValue.objects.create(title="Hidden", text="No.", is_active=False)
        page = self.client.get(reverse("shop:about"))
        self.assertContains(page, "Made in Islamabad")
        self.assertNotContains(page, "Hidden")

    def test_hero_film_can_be_uploaded(self):
        info = StoreInfo.load()
        info.hero_video = SimpleUploadedFile("film.mp4", b"x", content_type="video/mp4")
        info.save()
        home = self.client.get(reverse("shop:home"))
        self.assertContains(home, "hero/film")
        self.assertNotContains(home, "img/hero/hero.mp4")
