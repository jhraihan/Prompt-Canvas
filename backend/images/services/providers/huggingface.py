import io
import logging

from django.conf import settings
from huggingface_hub import InferenceClient
from huggingface_hub.errors import (
    BadRequestError,
    GatedRepoError,
    HfHubHTTPError,
    InferenceTimeoutError,
    OverloadedError,
    RepositoryNotFoundError,
)

from images.constants import quality_profile
from images.exceptions import (
    GenerationError,
    ProviderAuthError,
    ProviderRateLimited,
    ProviderRejectedPrompt,
    ProviderTimeout,
    ProviderUnavailable,
)

from .base import GeneratedAsset, GenerationRequest, ImageProvider

logger = logging.getLogger("promptcanvas.provider.huggingface")


class HuggingFaceProvider(ImageProvider):
    name = "huggingface"

    def __init__(self, token=None, model=None, provider=None, timeout=None):
        self.token = token if token is not None else settings.HF_TOKEN
        self.model = model or settings.HF_MODEL
        self.routing = provider or settings.HF_PROVIDER
        self.timeout = timeout or settings.HF_TIMEOUT
        if not self.token:
            raise ProviderAuthError("HF_TOKEN is not set")

    def describe(self):
        return {"provider": self.name, "model": self.model}

    def _client(self):
        return InferenceClient(
            provider=self.routing,
            api_key=self.token,
            timeout=self.timeout,
        )

    def generate(self, request: GenerationRequest) -> GeneratedAsset:
        model = request.model or self.model
        params = quality_profile(model, request.quality)
        try:
            image = self._client().text_to_image(
                request.prompt,
                model=model,
                width=request.width,
                height=request.height,
                **params,
            )
        except InferenceTimeoutError as exc:
            logger.warning("Hugging Face timed out after %ss", self.timeout)
            raise ProviderTimeout(str(exc)) from exc
        except OverloadedError as exc:
            logger.warning("Hugging Face reported the model as overloaded")
            raise ProviderUnavailable(str(exc)) from exc
        except (GatedRepoError, RepositoryNotFoundError) as exc:
            logger.error("Model %s is gated or missing for this token", self.model)
            raise ProviderAuthError(str(exc)) from exc
        except BadRequestError as exc:
            logger.info("Hugging Face rejected the request")
            raise ProviderRejectedPrompt(str(exc)) from exc
        except HfHubHTTPError as exc:
            raise self._translate_http_error(exc) from exc
        except Exception as exc:
            logger.exception("Unexpected Hugging Face failure")
            raise GenerationError(str(exc)) from exc

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return GeneratedAsset(
            image_bytes=buffer.getvalue(),
            content_type="image/png",
            provider=self.name,
            model=model,
            width=image.width,
            height=image.height,
        )

    def _translate_http_error(self, exc):
        status = getattr(getattr(exc, "response", None), "status_code", None)
        logger.error("Hugging Face HTTP %s for model %s", status, self.model)
        if status in (401, 403):
            return ProviderAuthError(f"HTTP {status}")
        if status == 429:
            return ProviderRateLimited(f"HTTP {status}")
        if status in (408, 504):
            return ProviderTimeout(f"HTTP {status}")
        if status in (400, 422):
            return ProviderRejectedPrompt(f"HTTP {status}")
        if status is not None and status >= 500:
            return ProviderUnavailable(f"HTTP {status}")
        return GenerationError(f"HTTP {status}")
