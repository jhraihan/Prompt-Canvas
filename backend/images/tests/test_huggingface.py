import io

import pytest
from huggingface_hub.errors import (
    BadRequestError,
    GatedRepoError,
    HfHubHTTPError,
    InferenceTimeoutError,
    OverloadedError,
    RepositoryNotFoundError,
)
from PIL import Image

from images.exceptions import (
    GenerationError,
    ProviderAuthError,
    ProviderRateLimited,
    ProviderRejectedPrompt,
    ProviderTimeout,
    ProviderUnavailable,
)
from images.services.providers.base import GenerationRequest
from images.services.providers.huggingface import HuggingFaceProvider

REQUEST = GenerationRequest(
    prompt="a harbour at dawn", width=1024, height=1024, quality="standard"
)


@pytest.fixture
def provider(settings):
    settings.HF_TOKEN = "hf_test_token"
    settings.HF_MODEL = "black-forest-labs/FLUX.1-schnell"
    return HuggingFaceProvider()


class FakeClient:
    def __init__(self, *, image=None, error=None):
        self._image = image
        self._error = error
        self.calls = []

    def text_to_image(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        if self._error is not None:
            raise self._error
        return self._image


def attach(monkeypatch, provider, **kwargs):
    client = FakeClient(**kwargs)
    monkeypatch.setattr(provider, "_client", lambda: client)
    return client


class TestSuccessfulGeneration:
    def test_returns_png_bytes_from_the_returned_image(self, provider, monkeypatch):
        attach(monkeypatch, provider, image=Image.new("RGB", (1024, 1024), "navy"))

        asset = provider.generate(REQUEST)

        assert asset.image_bytes.startswith(b"\x89PNG")
        assert asset.content_type == "image/png"
        assert asset.extension == "png"
        assert asset.provider == "huggingface"
        assert asset.model == "black-forest-labs/FLUX.1-schnell"

    def test_reports_the_dimensions_of_the_actual_image(self, provider, monkeypatch):
        attach(monkeypatch, provider, image=Image.new("RGB", (512, 768), "navy"))

        asset = provider.generate(REQUEST)

        assert (asset.width, asset.height) == (512, 768)

    def test_bytes_decode_back_to_an_image(self, provider, monkeypatch):
        attach(monkeypatch, provider, image=Image.new("RGB", (64, 64), "red"))

        asset = provider.generate(REQUEST)

        assert Image.open(io.BytesIO(asset.image_bytes)).size == (64, 64)

    def test_passes_prompt_model_and_dimensions_through(self, provider, monkeypatch):
        client = attach(monkeypatch, provider, image=Image.new("RGB", (8, 8)))

        provider.generate(REQUEST)

        call = client.calls[0]
        assert call["prompt"] == "a harbour at dawn"
        assert call["model"] == "black-forest-labs/FLUX.1-schnell"
        assert call["width"] == 1024
        assert call["height"] == 1024

    def test_applies_the_sampler_profile_for_the_model(self, provider, monkeypatch):
        client = attach(monkeypatch, provider, image=Image.new("RGB", (8, 8)))

        provider.generate(REQUEST)

        call = client.calls[0]
        assert call["num_inference_steps"] == 4
        assert call["guidance_scale"] == 0.0

    def test_hd_requests_more_steps_than_standard(self, provider, monkeypatch):
        client = attach(monkeypatch, provider, image=Image.new("RGB", (8, 8)))

        provider.generate(REQUEST)
        provider.generate(GenerationRequest(prompt="x", width=8, height=8, quality="hd"))

        assert (
            client.calls[1]["num_inference_steps"]
            > client.calls[0]["num_inference_steps"]
        )


class TestFailureTranslation:
    @staticmethod
    def _response(status, message="upstream detail"):
        import httpx

        return httpx.Response(
            status,
            content=message.encode(),
            request=httpx.Request("POST", "https://router.huggingface.co/test"),
        )

    @staticmethod
    def _http_error(status, message="upstream detail"):
        import httpx

        response = httpx.Response(
            status,
            content=message.encode(),
            request=httpx.Request("POST", "https://router.huggingface.co/test"),
        )
        return HfHubHTTPError(message, response=response)

    def test_timeout(self, provider, monkeypatch):
        attach(monkeypatch, provider, error=InferenceTimeoutError("stalled"))
        with pytest.raises(ProviderTimeout):
            provider.generate(REQUEST)

    def test_overloaded(self, provider, monkeypatch):
        attach(monkeypatch, provider, error=OverloadedError("busy"))
        with pytest.raises(ProviderUnavailable):
            provider.generate(REQUEST)

    def test_gated_repo(self, provider, monkeypatch):
        attach(
            monkeypatch,
            provider,
            error=GatedRepoError("gated", response=self._response(403)),
        )
        with pytest.raises(ProviderAuthError):
            provider.generate(REQUEST)

    def test_missing_repo(self, provider, monkeypatch):
        attach(
            monkeypatch,
            provider,
            error=RepositoryNotFoundError("gone", response=self._response(404)),
        )
        with pytest.raises(ProviderAuthError):
            provider.generate(REQUEST)

    def test_bad_request_is_a_rejected_prompt(self, provider, monkeypatch):
        attach(
            monkeypatch,
            provider,
            error=BadRequestError("no", response=self._response(400)),
        )
        with pytest.raises(ProviderRejectedPrompt):
            provider.generate(REQUEST)

    def test_http_error_is_routed_through_the_translator(self, provider, monkeypatch):
        attach(monkeypatch, provider, error=self._http_error(429))
        with pytest.raises(ProviderRateLimited):
            provider.generate(REQUEST)

    def test_unexpected_exception_becomes_a_generation_error(self, provider, monkeypatch):
        attach(monkeypatch, provider, error=RuntimeError("something odd"))
        with pytest.raises(GenerationError):
            provider.generate(REQUEST)

    def test_a_failure_never_carries_the_response_body(self, provider, monkeypatch):
        attach(
            monkeypatch,
            provider,
            error=self._http_error(401, "token hf_leaked_value rejected"),
        )
        with pytest.raises(ProviderAuthError) as caught:
            provider.generate(REQUEST)
        assert "hf_leaked_value" not in str(caught.value)

    def test_user_message_is_safe_for_display(self, provider, monkeypatch):
        attach(monkeypatch, provider, error=RuntimeError("Traceback: /srv/app/x.py"))
        with pytest.raises(GenerationError) as caught:
            provider.generate(REQUEST)
        assert "Traceback" not in caught.value.user_message
        assert "/srv/app" not in caught.value.user_message


class TestConstruction:
    def test_refuses_to_start_without_a_token(self, settings):
        settings.HF_TOKEN = ""
        with pytest.raises(ProviderAuthError):
            HuggingFaceProvider()

    def test_explicit_arguments_override_settings(self, settings):
        settings.HF_TOKEN = "from-settings"
        provider = HuggingFaceProvider(token="explicit", model="acme/model")
        assert provider.token == "explicit"
        assert provider.model == "acme/model"

    def test_describe_exposes_no_credentials(self, provider):
        description = provider.describe()
        assert set(description) == {"provider", "model"}
        assert "hf_test_token" not in str(description)

    def test_client_is_configured_from_settings(self, settings, monkeypatch):
        settings.HF_TOKEN = "hf_test_token"
        settings.HF_PROVIDER = "auto"
        settings.HF_TIMEOUT = 90
        captured = {}

        def fake_client(**kwargs):
            captured.update(kwargs)
            return object()

        monkeypatch.setattr(
            "images.services.providers.huggingface.InferenceClient", fake_client
        )
        HuggingFaceProvider()._client()

        assert captured["api_key"] == "hf_test_token"
        assert captured["provider"] == "auto"
        assert captured["timeout"] == 90
