from django.db import models
from django.urls import reverse
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


class Branch(models.Model):
    """A physical store location, shown on the Contact page and in the footer."""

    name = models.CharField(max_length=100, help_text="e.g. DHA II")
    city = models.CharField(max_length=100, default="Islamabad")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    opening_hours = models.CharField(max_length=200, blank=True)
    map_embed_url = models.URLField(blank=True, help_text="Not used any more. The map is built from the latitude and longitude below.")
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


class HeroSlide(models.Model):
    """A photo in the home page hero slideshow. Product-only imagery (see design.md)."""

    class Focus(models.TextChoices):
        CENTER = "center", "Centre"
        TOP = "top", "Top"
        BOTTOM = "bottom", "Bottom"
        LEFT = "left", "Left"
        RIGHT = "right", "Right"

    image = models.ImageField(upload_to="hero/", help_text="Wide or square photo, at least 1600px. One piece per frame.")
    caption = models.CharField(max_length=80, blank=True, help_text="Heading shown on the slide, e.g. “Bridal Bangles”.")
    subtitle = models.CharField(max_length=160, blank=True, help_text="One short line under the heading.")
    tone = models.CharField(
        max_length=5, choices=[("light", "Light photo (dark text)"), ("dark", "Dark photo (cream text)")],
        default="light", help_text="Pick the text colour that reads best on this photo.",
    )
    link = models.CharField(max_length=200, blank=True, help_text="Optional page link, e.g. /collections/?category=bangles")
    focus = models.CharField(
        max_length=10, choices=Focus.choices, default=Focus.CENTER,
        help_text="Which part of the photo to keep in view when it is cropped.",
    )
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.caption or f"Slide {self.pk}"

    @property
    def url(self):
        return self.image.url


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    summary = models.CharField(max_length=160, help_text="One short line, shown on the home page.")
    description = models.TextField(blank=True, help_text="A few sentences, shown on the Services page.")
    turnaround = models.CharField(max_length=60, blank=True, help_text='For example "Same day" or "3 to 5 days".')
    price_note = models.CharField(max_length=60, blank=True, help_text='For example "From Rs 1,500" or "Complimentary".')
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    @property
    def wa_text(self):
        return f"Hello, I would like to enquire about your {self.name.lower()} service."
