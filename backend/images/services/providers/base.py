from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    width: int
    height: int
    quality: str
    model: str | None = None


@dataclass(frozen=True)
class GeneratedAsset:
    image_bytes: bytes
    content_type: str
    provider: str
    model: str
    width: int
    height: int

    @property
    def extension(self):
        return {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(
            self.content_type, "png"
        )


class ImageProvider(ABC):
    name = "base"

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GeneratedAsset:
        """Produce an image, or raise a `images.exceptions.GenerationError`."""

    @abstractmethod
    def describe(self) -> dict:
        """Non-sensitive provider metadata for the client. Never include tokens."""
