from django.conf import settings

from .base import ImageStorage, StoredImage
from .local import LocalImageStorage

STORAGES = {LocalImageStorage.name: LocalImageStorage}

__all__ = ["STORAGES", "ImageStorage", "LocalImageStorage", "StoredImage", "get_storage"]


def get_storage(name=None):
    key = name or settings.IMAGE_STORAGE
    try:
        storage_class = STORAGES[key]
    except KeyError as exc:
        raise KeyError(
            f"Unknown IMAGE_STORAGE {key!r}. Available: {sorted(STORAGES)}"
        ) from exc
    return storage_class()
