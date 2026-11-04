from urllib.parse import parse_qsl, urlsplit

from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    image_url = models.URLField(max_length=500, blank=True, help_text="Optional: an image link, used when no file is uploaded.")
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:collections") + f"?category={self.slug}"

    @property
    def photo_url(self):
        return self.image.url if self.image else self.image_url


class Product(models.Model):
    class Metal(models.TextChoices):
        GOLD = "gold", "Gold"
        SILVER = "silver", "Silver"
        PLATINUM = "platinum", "Platinum"
        ROSE_GOLD = "rose_gold", "Rose Gold"
        WHITE_GOLD = "white_gold", "White Gold"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    description = models.TextField(blank=True)
    metal = models.CharField(max_length=20, choices=Metal.choices, default=Metal.GOLD)
    purity = models.CharField(max_length=30, blank=True, help_text="e.g. 22K, 18K, 925 Sterling")
    weight_grams = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    gemstone = models.CharField(max_length=100, blank=True, help_text="e.g. Diamond, Ruby, Kundan")
    price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Leave empty to show 'Price on request'.",
    )
    image = models.ImageField(upload_to="products/", blank=True, help_text="Main product photo.")
    image_url = models.URLField(max_length=500, blank=True, help_text="Optional: an image link, used when no file is uploaded.")
    is_featured = models.BooleanField(default=False, help_text="Show on the home page.")
    is_active = models.BooleanField(default=True, help_text="Untick to hide from the website.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "product"
            slug, n = base, 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:product_detail", args=[self.slug])

    @property
    def photo_url(self):
        return self.image.url if self.image else self.image_url

    @property
    def price_label(self):
        return f"Rs {self.price:,.0f}" if self.price is not None else "Price on request"

    @property
    def weight_label(self):
        if self.weight_grams is None:
            return ""
        text = f"{self.weight_grams:f}"
        return text.rstrip("0").rstrip(".") if "." in text else text

    @property
    def photo_urls(self):
        """Main photo first, then the gallery."""
        urls = [self.photo_url] if self.photo_url else []
        urls += [g.photo_url for g in self.gallery.all() if g.photo_url]
        return urls


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="products/gallery/", blank=True)
    image_url = models.URLField(max_length=500, blank=True, help_text="Optional: an image link, used when no file is uploaded.")
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"Image for {self.product}"

    @property
    def photo_url(self):
        return self.image.url if self.image else self.image_url


class Enquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    message = models.TextField()
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="enquiries"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    notes = models.TextField(blank=True, help_text="Internal notes (not shown to customer).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "enquiries"

    def __str__(self):
        return f"{self.name} ({self.created_at:%d %b %Y})"


HEX = RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Use a colour like #B8975A.")

SANS_FONTS = ["Montserrat", "Inter", "Jost", "Poppins", "DM Sans", "Raleway", "Lato", "Work Sans", "Manrope", "Nunito Sans"]
SERIF_FONTS = ["Playfair Display", "Cormorant Garamond", "Lora", "Libre Baskerville", "EB Garamond", "Marcellus",
               "DM Serif Display", "Bodoni Moda", "Cinzel"]


ALL_FONTS = SANS_FONTS + SERIF_FONTS
# Weights Google Fonts really has, for the few fonts that lack some of 400, 500 and 600. Asking for a missing weight makes
# Google refuse the whole request, so only weights that exist are asked for.
ONLY_REGULAR = {"Marcellus", "DM Serif Display", "Lato", "Libre Baskerville"}


def _choices(names=None):
    """Every font can be used for any job, shown in two groups so the list stays easy to scan."""
    return [("Sans-serif", [(n, n) for n in SANS_FONTS]), ("Serif", [(n, n) for n in SERIF_FONTS])]


def _rgb(hex_color):
    h = hex_color.lstrip("#")
    return ", ".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


COLS_DESKTOP = [(2, "2"), (3, "3"), (4, "4")]
COLS_MOBILE = [(1, "1"), (2, "2")]
THEMES = [("light", "Light"), ("dark", "Dark")]


class StoreInfo(models.Model):
    """Single editable record with the brand's general details and About text."""

    name = models.CharField(max_length=120, default="Patiala Jewelers")
    descriptor = models.CharField(max_length=120, default="Gold & Diamonds")
    tagline = models.CharField(max_length=200, default="Where love meets gold.")
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(
        max_length=20, blank=True, help_text="Number with country code, digits only, e.g. 923001234567"
    )
    email = models.EmailField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    pinterest_url = models.URLField(blank=True)
    x_url = models.URLField("X (Twitter) URL", blank=True)

    # ----- Brand colours. The 60 / 30 / 10 rule: light 60%, dark 30%, gold 10%. -----
    color_light = models.CharField("Light (page background)", max_length=7, default="#FAF8F3", validators=[HEX])
    color_dark = models.CharField("Dark (text and dark bands)", max_length=7, default="#161513", validators=[HEX])
    color_gold = models.CharField("Gold (logo and accents)", max_length=7, default="#B8975A", validators=[HEX])
    color_gold_light = models.CharField("Gold on dark", max_length=7, default="#C9A96A", validators=[HEX])
    color_gold_deep = models.CharField("Gold for small text", max_length=7, default="#8A6D35", validators=[HEX])
    color_cream = models.CharField("Text on dark", max_length=7, default="#F3EFE6", validators=[HEX])

    # ----- Fonts: a primary sans, a secondary serif, and the face used for the logo wordmark. -----
    font_primary = models.CharField("Primary font", max_length=40, choices=_choices(), default="Montserrat",
                                    help_text="Headings, names, buttons and small labels.")
    heading_weight = models.PositiveSmallIntegerField(
        "Heading weight", choices=[(400, "Regular"), (500, "Medium"), (600, "Semibold")], default=500)
    font_secondary = models.CharField("Secondary font", max_length=40, choices=_choices(), default="Playfair Display",
                                      help_text="Paragraphs and descriptions.")
    font_wordmark = models.CharField("Logo wordmark font", max_length=40, choices=_choices(), default="Playfair Display",
                                     help_text="The PATIALA lettering next to the monogram.")

    # ----- Logo -----
    logo = models.ImageField(
        upload_to="brand/", blank=True,
        help_text="Optional monogram (SVG or PNG, transparent background). Leave empty to use the built-in gold monogram.",
    )
    favicon = models.ImageField(upload_to="brand/", blank=True, help_text="Optional browser-tab icon. Square PNG, at least 64 px.")

    # ----- Home page hero slider (the slides themselves are under Hero slides) -----
    hero_autoplay = models.BooleanField("Slide automatically", default=True)
    hero_interval = models.PositiveSmallIntegerField("Seconds per slide", default=6, help_text="Between 3 and 20.")
    hero_transition = models.CharField("Transition", max_length=10, default="slide",
                                       choices=[("slide", "Slide"), ("fade", "Fade")])
    hero_show_arrows = models.BooleanField("Show arrows", default=True)
    hero_show_dots = models.BooleanField("Show dots", default=True)

    # ----- Turn parts of the site on or off -----
    show_preloader = models.BooleanField("Intro screen when the site opens", default=True)
    show_whatsapp_button = models.BooleanField("Floating WhatsApp button", default=True)

    # ----- About page and the Our Story section -----
    about_heading = models.CharField(max_length=200, default="Our Story")
    about_text = models.TextField(blank=True)
    about_image = models.ImageField(
        upload_to="store/", blank=True,
        help_text="Wide photo. Used behind the Our Story section on the home page and on the About page.",
    )
    about_image_mobile = models.ImageField(
        upload_to="store/", blank=True,
        help_text="Optional portrait photo for phones. If you leave it empty, the main photo is used on phones too.",
    )
    show_about_story = models.BooleanField("About page: story", default=True)
    show_about_promises = models.BooleanField("About page: promises", default=True)
    show_about_closing = models.BooleanField("About page: closing line", default=True)

    class Meta:
        verbose_name = "store information"
        verbose_name_plural = "store information"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1  # always a single row
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # never delete the store record

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def socials(self):
        pairs = [("Instagram", self.instagram_url), ("Facebook", self.facebook_url), ("TikTok", self.tiktok_url),
                 ("YouTube", self.youtube_url), ("Pinterest", self.pinterest_url), ("X", self.x_url)]
        return [(label, url) for label, url in pairs if url]

    @staticmethod
    def _hex(value, default):
        return value if HEX.regex.match(value or "") else default

    @staticmethod
    def _font(value, allowed, default):
        return value if value in allowed else default

    @property
    def theme_css(self):
        """CSS custom properties for the colours, fonts and heading weight chosen in the admin.
        Every value is checked against the allowed hex pattern or font list, so the result is safe to print inside <style>."""
        light = self._hex(self.color_light, "#FAF8F3")
        dark = self._hex(self.color_dark, "#161513")
        cream = self._hex(self.color_cream, "#F3EFE6")
        sans = self._font(self.font_primary, ALL_FONTS, "Montserrat")
        serif = self._font(self.font_secondary, ALL_FONTS, "Playfair Display")
        brand = self._font(self.font_wordmark, ALL_FONTS, "Playfair Display")
        weight = self.heading_weight if self.heading_weight in (400, 500, 600) else 500
        return mark_safe(
            f"--soft-white:{light};--soft-black:{dark};--gold:{self._hex(self.color_gold, '#B8975A')};"
            f"--gold-light:{self._hex(self.color_gold_light, '#C9A96A')};--gold-deep:{self._hex(self.color_gold_deep, '#8A6D35')};--cream:{cream};"
            f"--paper-rgb:{_rgb(light)};--ink-rgb:{_rgb(dark)};--cream-rgb:{_rgb(cream)};"
            f"--font-display:'{sans}',system-ui,sans-serif;--font-body:'{sans}',system-ui,sans-serif;"
            f"--font-serif:'{serif}',Georgia,serif;--font-brand:'{brand}',Georgia,serif;--heading-weight:{weight};"
        )

    @property
    def fonts_url(self):
        """One Google Fonts request for every face the site uses."""
        wanted = {}
        for field, default, weights in (("font_primary", "Montserrat", (400, 500, 600)), ("font_secondary", "Playfair Display", (400,)),
                                        ("font_wordmark", "Playfair Display", (400,))):
            name = self._font(getattr(self, field), ALL_FONTS, default)
            wanted.setdefault(name, set()).update(weights if name not in ONLY_REGULAR else (400,))
        parts = [f"family={name.replace(' ', '+')}:wght@{';'.join(str(n) for n in sorted(sizes))}" for name, sizes in wanted.items()]
        return "https://fonts.googleapis.com/css2?" + "&".join(parts) + "&display=swap"

    @property
    def favicon_url(self):
        return self.favicon.url if self.favicon else ""


class Branch(models.Model):
    """A physical store location, shown on the Contact page and in the footer."""

    name = models.CharField(max_length=100, help_text="e.g. DHA II")
    city = models.CharField(max_length=100, default="Islamabad")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    opening_hours = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="In Google Maps, right-click the shop and click the first number. Example: 33.720000")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="The second number. Example: 73.056000")
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "branches"

    def __str__(self):
        return f"{self.name}, {self.city}"

    @property
    def maps_url(self):
        from urllib.parse import quote_plus
        return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"Patiala Jewelers {self.name} {self.city}")


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, blank=True, db_index=True)
    summary = models.CharField(max_length=160, help_text="One short line, shown on cards.")
    intro = models.CharField(max_length=200, blank=True, help_text="One line under the title on the service page.")
    description = models.TextField(blank=True, help_text="A few sentences, shown on the service page.")
    includes = models.TextField(blank=True, help_text="What is included. One item per line.")
    process = models.TextField(blank=True, help_text='How it works. One step per line, written as "Title | a short sentence".')
    image = models.ImageField(upload_to="services/", blank=True)
    image_url = models.URLField(max_length=500, blank=True, help_text="Optional: an image link, used when no file is uploaded.")
    turnaround = models.CharField(max_length=60, blank=True, help_text='For example "Same day" or "3 to 5 days".')
    price_note = models.CharField(max_length=60, blank=True, help_text='For example "From Rs 1,500" or "Complimentary".')
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:service_detail", args=[self.slug])

    @property
    def photo_url(self):
        return self.image.url if self.image else self.image_url

    @property
    def include_list(self):
        return [l.strip() for l in self.includes.splitlines() if l.strip()]

    @property
    def step_list(self):
        steps = []
        for line in self.process.splitlines():
            if line.strip():
                title, _, text = line.partition("|")
                steps.append({"title": title.strip(), "text": text.strip()})
        return steps

    @property
    def wa_text(self):
        return f"Hello, I would like to enquire about your {self.name.lower()} service."


class HomeSection(models.Model):
    """One block of the home page. The list of these, in display order, is the page below the hero."""

    class Kind(models.TextChoices):
        PRODUCTS = "products", "Products"
        SERVICES = "services", "Services"
        COLLECTIONS = "collections", "Categories"
        STORY = "story", "Image and text"
        LOCATIONS = "locations", "Locations"
        CONTACT = "contact", "Contact"

    class Layout(models.TextChoices):
        LEFT = "left", "Photo on the left"
        RIGHT = "right", "Photo on the right"
        BEHIND = "behind", "Photo behind the text"

    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.PRODUCTS)
    label = models.CharField("Small label", max_length=80, blank=True)
    title = models.CharField("Heading", max_length=120)
    text = models.TextField("Paragraph", max_length=600, blank=True)
    link = models.CharField(max_length=400, blank=True, help_text="A collections link such as /collections/?category=rings&metal=gold")
    button_label = models.CharField("Button words", max_length=60, blank=True)
    count = models.PositiveSmallIntegerField("How many to show", default=4)
    theme = models.CharField("Colour", max_length=5, choices=THEMES, default="light")
    cols = models.PositiveSmallIntegerField("Per row on a computer", choices=COLS_DESKTOP, default=4)
    cols_mobile = models.PositiveSmallIntegerField("Per row on a phone", choices=COLS_MOBILE, default=2)
    layout = models.CharField("Photo position", max_length=6, choices=Layout.choices, default=Layout.LEFT)
    image = models.ImageField(upload_to="home/", blank=True)
    image_mobile = models.ImageField(upload_to="home/", blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.title

    @property
    def params(self):
        """The filters in the link (category, metal, q), as the Collections page reads them."""
        return dict(parse_qsl(urlsplit(self.link).query))

    @property
    def summary(self):
        if self.kind in (self.Kind.PRODUCTS, self.Kind.SERVICES):
            return f"{self.get_kind_display()} · {self.cols} per row"
        return self.get_kind_display()


class ContentBlock(models.Model):
    """One editable line of text on the site. The rows are created from shop/content.py."""

    key = models.SlugField(max_length=80, unique=True)
    group = models.CharField(max_length=40)
    label = models.CharField(max_length=120)
    text = models.TextField(blank=True)

    class Meta:
        ordering = ["group", "id"]
        verbose_name = "page text"
        verbose_name_plural = "page text"

    def __str__(self):
        return self.label


class AboutValue(models.Model):
    """One of the short promises shown on the About page."""

    title = models.CharField(max_length=80)
    text = models.CharField(max_length=200)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.title


class HeroSlide(models.Model):
    """One slide of the home page hero. With more than one active slide the hero slides on its own."""

    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    class Align(models.TextChoices):
        LEFT = "left", "Left"
        CENTER = "center", "Centre"

    class Tint(models.TextChoices):
        NONE = "none", "None"
        SOFT = "soft", "Soft"
        MEDIUM = "medium", "Medium"

    name = models.CharField(max_length=100, help_text="Only you see this. For example: Eid collection.")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.IMAGE)
    image = models.ImageField("Image (desktop)", upload_to="hero/", blank=True,
                              help_text="Wide photo, at least 2000 px across.")
    image_mobile = models.ImageField("Image (phone)", upload_to="hero/", blank=True,
                                     help_text="Tall photo for phones, shown full screen. Falls back to the desktop image.")
    video = models.FileField("Video (desktop)", upload_to="hero/", blank=True, help_text="MP4, ideally under 8 MB.")
    video_mobile = models.FileField("Video (phone)", upload_to="hero/", blank=True,
                                    help_text="Optional tall video. Falls back to the desktop video.")
    poster = models.ImageField("Still image for the video", upload_to="hero/", blank=True,
                               help_text="Shown while the video loads. Optional.")

    show_text = models.BooleanField("Show text on this slide", default=True)
    heading = models.CharField(max_length=120, blank=True)
    text = models.CharField("Line under the heading", max_length=220, blank=True)
    button_label = models.CharField(max_length=40, blank=True, help_text="Leave empty for no button.")
    link = models.CharField("Link", max_length=300, blank=True,
                            help_text="Where the button goes, for example /collections/ or https://... With no button and no text, the whole slide becomes the link.")
    open_in_new_tab = models.BooleanField(default=False)
    text_color = models.CharField("Text colour on a computer", max_length=7, default="#161513", validators=[HEX])
    text_color_mobile = models.CharField("Text colour on a phone", max_length=7, blank=True, validators=[HEX],
                                         help_text="Leave empty to use the computer colour.")
    text_align = models.CharField("Text position on desktop", max_length=10, choices=Align.choices, default=Align.LEFT)
    tint = models.CharField("Darken the picture", max_length=10, choices=Tint.choices, default=Tint.NONE)

    seconds = models.PositiveSmallIntegerField("Seconds on screen", null=True, blank=True,
                                               help_text="Leave empty to use the default from Store information.")
    show_from = models.DateField("Show from", null=True, blank=True)
    show_until = models.DateField("Show until", null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        self.link = (self.link or "").strip()
        errors = {}
        if self.kind == self.Kind.IMAGE and not self.image:
            errors["image"] = "Add the image for this slide, or switch the type to Video."
        if self.kind == self.Kind.VIDEO and not self.video:
            errors["video"] = "Add the video for this slide, or switch the type to Image."
        if self.link and not self.link.startswith(("/", "http://", "https://", "tel:", "mailto:", "#")):
            errors["link"] = "Start the link with / (a page on this site) or https://"
        if self.button_label and not self.link:
            errors["link"] = "A button needs a link."
        if self.seconds is not None and not 3 <= self.seconds <= 20:
            errors["seconds"] = "Use a number between 3 and 20."
        if self.show_from and self.show_until and self.show_until < self.show_from:
            errors["show_until"] = "This date is before the start date."
        if errors:
            raise ValidationError(errors)

    @property
    def has_text(self):
        return bool(self.heading or self.text or (self.button_label and self.link))

    @staticmethod
    def _is_light(color):
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        return (0.299 * r + 0.587 * g + 0.114 * b) > 150

    @property
    def ink(self):
        return StoreInfo._hex(self.text_color, "#161513")

    @property
    def ink_mobile(self):
        return StoreInfo._hex(self.text_color_mobile, self.ink)

    @property
    def ink_style(self):
        """The text colours as CSS variables for this slide, plus the colour that reads on top of each (used when a button fills on hover).
        Both colours are checked against the hex pattern, so the result is safe to print inside style=""."""
        on = lambda c: "#161513" if self._is_light(c) else "#FAF8F3"
        return mark_safe(f"--ink:{self.ink};--on:{on(self.ink)};--ink-m:{self.ink_mobile};--on-m:{on(self.ink_mobile)}")

    @property
    def fade(self):
        """On a phone the words sit on a fade. Dark words get a light fade, light words a dark one."""
        return "light" if not self._is_light(self.ink_mobile) else "dark"

    @property
    def desktop_url(self):
        f = self.video if self.kind == self.Kind.VIDEO else self.image
        return f.url if f else ""

    @property
    def mobile_url(self):
        f = (self.video_mobile or self.video) if self.kind == self.Kind.VIDEO else (self.image_mobile or self.image)
        return f.url if f else ""

    @property
    def poster_url(self):
        return self.poster.url if self.poster else (self.image.url if self.image else "")

    @property
    def poster_mobile_url(self):
        return self.image_mobile.url if self.image_mobile else self.poster_url
