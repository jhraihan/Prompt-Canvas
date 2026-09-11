from django.conf import settings
from rest_framework import serializers

from .constants import (
    MAX_PROMPT_LENGTH,
    MIN_PROMPT_LENGTH,
    MODEL_CHOICES,
    QUALITY_CHOICES,
    QUALITY_STANDARD,
    SIZE_CHOICES,
    SIZE_SQUARE,
)
from .models import GeneratedImage, SavedPrompt, ShareLink


class GeneratedImageSerializer(serializers.ModelSerializer):
    download_filename = serializers.CharField(read_only=True)

    class Meta:
        model = GeneratedImage
        fields = (
            "id",
            "prompt",
            "image_url",
            "size",
            "quality",
            "provider",
            "model",
            "width",
            "height",
            "byte_size",
            "download_filename",
            "created_at",
        )
        read_only_fields = fields


class GenerationRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(
        max_length=MAX_PROMPT_LENGTH,
        min_length=MIN_PROMPT_LENGTH,
        trim_whitespace=True,
        error_messages={
            "blank": "Describe the image you want to generate.",
            "min_length": (
                f"Add a little more detail (at least {MIN_PROMPT_LENGTH} characters)."
            ),
            "max_length": f"Prompts are limited to {MAX_PROMPT_LENGTH} characters.",
            "required": "Describe the image you want to generate.",
        },
    )
    size = serializers.ChoiceField(
        choices=SIZE_CHOICES,
        default=SIZE_SQUARE,
        error_messages={"invalid_choice": "Pick one of the supported image sizes."},
    )
    quality = serializers.ChoiceField(
        choices=QUALITY_CHOICES,
        default=QUALITY_STANDARD,
        error_messages={"invalid_choice": "Pick one of the supported quality settings."},
    )
    model = serializers.ChoiceField(
        choices=MODEL_CHOICES,
        required=False,
        allow_null=True,
        error_messages={"invalid_choice": "Pick one of the supported models."},
    )

    def validate_prompt(self, value):
        if not value.strip():
            raise serializers.ValidationError("Describe the image you want to generate.")
        return value.strip()


class SavedPromptSerializer(serializers.ModelSerializer):
    display_label = serializers.CharField(read_only=True)

    class Meta:
        model = SavedPrompt
        fields = (
            "id",
            "prompt",
            "label",
            "display_label",
            "size",
            "quality",
            "use_count",
            "last_used_at",
            "created_at",
        )
        read_only_fields = ("id", "use_count", "last_used_at", "created_at")

    def validate_prompt(self, value):
        value = value.strip()
        if len(value) < MIN_PROMPT_LENGTH:
            raise serializers.ValidationError(
                f"A saved prompt needs at least {MIN_PROMPT_LENGTH} characters."
            )
        if len(value) > MAX_PROMPT_LENGTH:
            raise serializers.ValidationError(
                f"Prompts are limited to {MAX_PROMPT_LENGTH} characters."
            )
        return value

    def validate(self, attrs):
        prompt = attrs.get("prompt")
        if prompt is None:
            return attrs

        user = self.context["request"].user
        existing = SavedPrompt.objects.filter(user=user, prompt=prompt)
        if self.instance is not None:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError(
                {"prompt": "You have already saved this prompt."}
            )
        return attrs


class ShareLinkSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    active = serializers.BooleanField(source="is_active", read_only=True)

    class Meta:
        model = ShareLink
        fields = (
            "id",
            "token",
            "url",
            "active",
            "expires_at",
            "revoked_at",
            "view_count",
            "created_at",
        )
        read_only_fields = fields

    def get_url(self, obj):
        base = (getattr(settings, "FRONTEND_BASE_URL", "") or "").rstrip("/")
        return f"{base}/shared/{obj.token}"


class SharedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedImage
        fields = ("prompt", "image_url", "size", "width", "height", "created_at")
        read_only_fields = fields


class ShareLinkCreateSerializer(serializers.Serializer):
    expires_in_hours = serializers.IntegerField(
        required=False,
        default=168,
        min_value=1,
        max_value=720,
        error_messages={
            "min_value": "A share link must last at least an hour.",
            "max_value": "A share link can last at most 30 days.",
        },
    )


class BulkDeleteSerializer(serializers.Serializer):
    MAX_IDS = 100

    ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        max_length=MAX_IDS,
        error_messages={
            "empty": "Provide a list of image ids to delete.",
            "not_a_list": "Provide a list of image ids to delete.",
            "max_length": f"Delete at most {MAX_IDS} images at a time.",
            "required": "Provide a list of image ids to delete.",
        },
    )
