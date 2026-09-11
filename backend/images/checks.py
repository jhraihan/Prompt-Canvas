from django.conf import settings
from django.core.checks import Error, Warning, register

STUB_IN_PRODUCTION = "images.E001"
PROVIDER_UNKNOWN = "images.E002"
TOKEN_MISSING = "images.W001"  # noqa: S105 -- a check id, not a credential


def _is_production():
    if getattr(settings, "IS_NON_PRODUCTION", False):
        return False
    return not settings.DEBUG


@register("images")
def check_image_provider(app_configs, **kwargs):
    from .services.providers import PROVIDERS

    problems = []
    provider = getattr(settings, "IMAGE_PROVIDER", None)

    if provider not in PROVIDERS:
        problems.append(
            Error(
                f"IMAGE_PROVIDER is {provider!r}, which is not a registered provider.",
                hint=f"Set it to one of: {', '.join(sorted(PROVIDERS))}.",
                id=PROVIDER_UNKNOWN,
            )
        )
        return problems

    if provider == "stub" and _is_production():
        problems.append(
            Error(
                "IMAGE_PROVIDER is 'stub' with DEBUG off. The stub provider "
                "returns placeholder gradients, so every generation would look "
                "successful while producing a meaningless image.",
                hint=(
                    "Set IMAGE_PROVIDER=huggingface and HF_TOKEN in the "
                    "environment, then verify with `manage.py check_provider`. "
                    "To run a non-production environment deliberately, leave "
                    "DEBUG on."
                ),
                id=STUB_IN_PRODUCTION,
            )
        )

    if provider == "huggingface" and not getattr(settings, "HF_TOKEN", ""):
        problems.append(
            Warning(
                "IMAGE_PROVIDER is 'huggingface' but HF_TOKEN is empty. Every "
                "generation will fail with a provider authentication error.",
                hint="Set HF_TOKEN in the environment.",
                id=TOKEN_MISSING,
            )
        )

    return problems
