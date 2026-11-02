from django.db import models


class Visit(models.Model):
    """One page view on the public site."""

    visitor = models.CharField(max_length=32, db_index=True)
    path = models.CharField(max_length=300, db_index=True)
    referrer = models.CharField(max_length=200, blank=True)
    device = models.CharField(max_length=10, default="desktop")
    browser = models.CharField(max_length=20, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "visit"

    def __str__(self):
        return f"{self.path} ({self.created_at:%Y-%m-%d %H:%M})"


class ClickEvent(models.Model):
    """A tap on something we want to count: WhatsApp, a phone number, a social link, a hero slide and so on."""

    class Kind(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        CALL = "call", "Phone call"
        EMAIL = "email", "Email"
        SOCIAL = "social", "Social link"
        HERO = "hero", "Hero slide"
        FAVORITE = "favorite", "Saved to favorites"
        MAP = "map", "Map"
        OTHER = "other", "Other"

    visitor = models.CharField(max_length=32, db_index=True)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.OTHER, db_index=True)
    label = models.CharField(max_length=120, blank=True)
    target = models.CharField(max_length=300, blank=True)
    path = models.CharField(max_length=300, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "click"

    def __str__(self):
        return f"{self.get_kind_display()} {self.label}".strip()
