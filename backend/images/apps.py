from django.apps import AppConfig


class ImagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "images"
    verbose_name = "Generated images"

    def ready(self):
        from . import checks  # noqa: F401
