import logging

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from images.exceptions import StorageError

from .base import ImageStorage, StoredImage

logger = logging.getLogger("promptcanvas.storage")


class LocalImageStorage(ImageStorage):
    name = "local"

    def save(self, key, data, content_type):
        try:
            stored_key = default_storage.save(key, ContentFile(data))
        except OSError as exc:
            logger.exception("Failed to write %s to MEDIA_ROOT", key)
            raise StorageError(str(exc)) from exc
        return StoredImage(
            key=stored_key,
            url=self.url_for(stored_key),
            byte_size=len(data),
        )

    def delete(self, key):
        if not key:
            return
        try:
            if default_storage.exists(key):
                default_storage.delete(key)
        except OSError:
            logger.warning("Could not delete stored image %s", key)

    def url_for(self, key):
        url = default_storage.url(key)
        base = getattr(settings, "MEDIA_BASE_URL", "").rstrip("/")
        if base and url.startswith("/"):
            return f"{base}{url}"
        return url
