from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class StoredImage:
    key: str
    url: str
    byte_size: int


class ImageStorage(ABC):
    name = "base"

    @abstractmethod
    def save(self, key: str, data: bytes, content_type: str) -> StoredImage:
        """Persist bytes and return their public location."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a stored object. Must not raise if it is already gone."""

    @abstractmethod
    def url_for(self, key: str) -> str:
        """Public URL for a stored key."""
