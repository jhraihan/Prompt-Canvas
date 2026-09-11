import logging
import time
import uuid

from django.db import DatabaseError, transaction

from images.constants import parse_size
from images.exceptions import GenerationError, StorageError
from images.models import GeneratedImage

from .providers import GenerationRequest, get_provider
from .storage import get_storage

logger = logging.getLogger("promptcanvas.generation")


def _storage_key(user_id, extension):
    return f"generated/{user_id}/{uuid.uuid4().hex}.{extension}"


def generate_image(
    *, user, prompt, size, quality, model=None, provider=None, storage=None
):
    provider = provider or get_provider()
    storage = storage or get_storage()
    width, height = parse_size(size)

    started = time.monotonic()
    asset = provider.generate(
        GenerationRequest(
            prompt=prompt, width=width, height=height, quality=quality, model=model
        )
    )
    duration_ms = int((time.monotonic() - started) * 1000)

    stored = storage.save(
        _storage_key(user.pk, asset.extension), asset.image_bytes, asset.content_type
    )

    try:
        with transaction.atomic():
            image = GeneratedImage.objects.create(
                user=user,
                prompt=prompt,
                image_url=stored.url,
                storage_key=stored.key,
                size=size,
                quality=quality,
                provider=asset.provider,
                model=asset.model,
                width=asset.width,
                height=asset.height,
                byte_size=stored.byte_size,
                duration_ms=duration_ms,
            )
    except DatabaseError as exc:
        storage.delete(stored.key)
        logger.exception("Failed to persist generation metadata")
        raise StorageError(str(exc)) from exc

    logger.info(
        "Generated image id=%s user=%s provider=%s model=%s size=%s quality=%s in %sms",
        image.pk,
        user.pk,
        asset.provider,
        asset.model,
        size,
        quality,
        duration_ms,
    )
    return image


def delete_image(image):
    key = image.storage_key
    storage = get_storage()
    image.delete()
    storage.delete(key)


def provider_metadata():
    try:
        return get_provider().describe()
    except GenerationError:
        logger.warning("Active provider could not be initialised")
        return {"provider": None, "model": None}
