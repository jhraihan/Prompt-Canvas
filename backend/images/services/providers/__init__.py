from django.conf import settings

from .base import GeneratedAsset, GenerationRequest, ImageProvider
from .huggingface import HuggingFaceProvider
from .stub import StubProvider

PROVIDERS = {
    HuggingFaceProvider.name: HuggingFaceProvider,
    StubProvider.name: StubProvider,
}

__all__ = [
    "PROVIDERS",
    "GeneratedAsset",
    "GenerationRequest",
    "HuggingFaceProvider",
    "ImageProvider",
    "StubProvider",
    "get_provider",
]


def get_provider(name=None):
    key = name or settings.IMAGE_PROVIDER
    try:
        provider_class = PROVIDERS[key]
    except KeyError as exc:
        raise KeyError(
            f"Unknown IMAGE_PROVIDER {key!r}. Available: {sorted(PROVIDERS)}"
        ) from exc
    return provider_class()
