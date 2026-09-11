from django.contrib import admin

from .models import GeneratedImage


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "short_prompt",
        "size",
        "quality",
        "provider",
        "created_at",
    )
    list_filter = ("provider", "size", "quality", "created_at")
    search_fields = ("prompt", "user__email")
    readonly_fields = (
        "created_at",
        "updated_at",
        "storage_key",
        "byte_size",
        "duration_ms",
    )
    date_hierarchy = "created_at"

    @admin.display(description="Prompt")
    def short_prompt(self, obj):
        return obj.prompt[:60]
