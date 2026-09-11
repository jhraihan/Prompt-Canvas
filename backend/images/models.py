from django.conf import settings
from django.db import models

from .constants import QUALITY_CHOICES, SIZE_CHOICES


class GeneratedImage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="images",
    )
    prompt = models.TextField()
    image_url = models.URLField(max_length=500)
    storage_key = models.CharField(max_length=300)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES)
    quality = models.CharField(max_length=20, choices=QUALITY_CHOICES)
    provider = models.CharField(max_length=50)
    model = models.CharField(max_length=120)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    byte_size = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["user", "-created_at"], name="image_user_recent_idx"),
        ]

    def __str__(self):
        preview = self.prompt[:40]
        return (
            f"{preview}... ({self.size})"
            if len(self.prompt) > 40
            else f"{preview} ({self.size})"
        )

    @property
    def download_filename(self):
        words = "".join(
            c if c.isalnum() or c.isspace() else " " for c in self.prompt
        ).split()[:6]
        slug = "-".join(w.lower() for w in words) or "image"
        stamp = self.created_at.strftime("%Y%m%d-%H%M%S") if self.created_at else "draft"
        return f"promptcanvas-{slug}-{stamp}.png"


class SavedPrompt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_prompts",
    )
    prompt = models.TextField()
    label = models.CharField(
        max_length=80,
        blank=True,
        help_text="Optional short name. Falls back to the start of the prompt.",
    )
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True)
    quality = models.CharField(max_length=20, choices=QUALITY_CHOICES, blank=True)
    use_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "prompt"], name="unique_saved_prompt_per_user"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="saved_user_recent_idx"),
        ]

    def __str__(self):
        return self.display_label

    @property
    def display_label(self):
        if self.label:
            return self.label
        return self.prompt[:60] + ("..." if len(self.prompt) > 60 else "")

    def record_use(self):
        from django.utils import timezone

        self.use_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=["use_count", "last_used_at"])


class ShareLink(models.Model):
    image = models.ForeignKey(
        GeneratedImage,
        on_delete=models.CASCADE,
        related_name="share_links",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"share of image {self.image_id}"

    @staticmethod
    def new_token():
        import secrets

        return secrets.token_urlsafe(32)

    @property
    def is_expired(self):
        from django.utils import timezone

        return timezone.now() >= self.expires_at

    @property
    def is_active(self):
        return self.revoked_at is None and not self.is_expired

    def revoke(self):
        from django.utils import timezone

        if self.revoked_at is None:
            self.revoked_at = timezone.now()
            self.save(update_fields=["revoked_at"])

    def record_view(self):
        from django.db.models import F

        type(self).objects.filter(pk=self.pk).update(view_count=F("view_count") + 1)
