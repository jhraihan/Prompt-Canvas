import pytest
from django.db import DatabaseError

from images.constants import parse_size, quality_profile
from images.exceptions import (
    ProviderAuthError,
    ProviderRateLimited,
    ProviderRejectedPrompt,
    ProviderTimeout,
    ProviderUnavailable,
    StorageError,
)
from images.models import GeneratedImage
from images.services.generation import generate_image
from images.services.providers import StubProvider, get_provider
from images.services.providers.base import GenerationRequest
from images.services.storage import get_storage


class TestSizeAndQuality:
    @pytest.mark.parametrize(
        "size,expected",
        [
            ("1024x1024", (1024, 1024)),
            ("1024x1536", (1024, 1536)),
            ("1536x1024", (1536, 1024)),
        ],
    )
    def test_parse_size(self, size, expected):
        assert parse_size(size) == expected

    def test_schnell_uses_few_steps_and_no_guidance(self):
        profile = quality_profile("black-forest-labs/FLUX.1-schnell", "standard")
        assert profile["num_inference_steps"] == 4
        assert profile["guidance_scale"] == 0.0

    def test_dev_uses_guidance(self):
        profile = quality_profile("black-forest-labs/FLUX.1-dev", "standard")
        assert profile["guidance_scale"] > 0

    def test_hd_costs_more_steps_than_standard(self):
        for model in ("FLUX.1-schnell", "FLUX.1-dev", "some/other-model"):
            standard = quality_profile(model, "standard")["num_inference_steps"]
            hd = quality_profile(model, "hd")["num_inference_steps"]
            assert hd > standard, model

    def test_unknown_model_falls_back_to_defaults(self):
        assert quality_profile("acme/unknown", "standard")["num_inference_steps"] == 25

    def test_returned_profile_is_a_copy(self):
        profile = quality_profile("FLUX.1-schnell", "standard")
        profile["num_inference_steps"] = 999
        assert quality_profile("FLUX.1-schnell", "standard")["num_inference_steps"] == 4


class TestProviderRegistry:
    def test_configured_provider_is_built(self, settings):
        settings.IMAGE_PROVIDER = "stub"
        assert isinstance(get_provider(), StubProvider)

    def test_unknown_provider_raises(self, settings):
        settings.IMAGE_PROVIDER = "midjourney"
        with pytest.raises(KeyError, match="Unknown IMAGE_PROVIDER"):
            get_provider()

    def test_describe_has_no_credentials(self):
        assert set(StubProvider().describe()) == {"provider", "model"}


class TestStubProvider:
    def test_produces_png_of_requested_size(self):
        asset = StubProvider().generate(
            GenerationRequest(prompt="a fox", width=1024, height=1536, quality="standard")
        )
        assert asset.image_bytes.startswith(b"\x89PNG")
        assert (asset.width, asset.height) == (1024, 1536)
        assert asset.extension == "png"

    def test_is_deterministic_for_the_same_prompt(self):
        provider = StubProvider()
        request = GenerationRequest(
            prompt="a fox", width=64, height=64, quality="standard"
        )
        assert (
            provider.generate(request).image_bytes
            == provider.generate(request).image_bytes
        )


class TestHuggingFaceProvider:
    def test_refuses_to_start_without_a_token(self, settings):
        from images.services.providers.huggingface import HuggingFaceProvider

        settings.HF_TOKEN = ""
        with pytest.raises(ProviderAuthError):
            HuggingFaceProvider()

    @staticmethod
    def _http_error(status, message="upstream said no"):
        import httpx
        from huggingface_hub.errors import HfHubHTTPError

        response = httpx.Response(
            status,
            content=message.encode(),
            request=httpx.Request("POST", "https://router.huggingface.co/test"),
        )
        return HfHubHTTPError(message, response=response)

    @pytest.mark.parametrize(
        "status,expected",
        [
            (401, ProviderAuthError),
            (403, ProviderAuthError),
            (429, ProviderRateLimited),
            (504, ProviderTimeout),
            (422, ProviderRejectedPrompt),
            (500, ProviderUnavailable),
            (503, ProviderUnavailable),
        ],
    )
    def test_http_errors_map_to_domain_errors(self, settings, status, expected):
        from images.services.providers.huggingface import HuggingFaceProvider

        settings.HF_TOKEN = "hf_test"
        provider = HuggingFaceProvider()
        translated = provider._translate_http_error(self._http_error(status))
        assert isinstance(translated, expected)

    def test_translated_error_carries_no_response_body(self, settings):
        from images.services.providers.huggingface import HuggingFaceProvider

        settings.HF_TOKEN = "hf_test"
        error = self._http_error(401, "token hf_leaked is invalid")
        translated = HuggingFaceProvider()._translate_http_error(error)
        assert "hf_leaked" not in str(translated)


class TestStorage:
    def test_round_trip(self, db, media_root):
        storage = get_storage()
        stored = storage.save("generated/1/test.png", b"\x89PNG-data", "image/png")
        assert stored.byte_size == len(b"\x89PNG-data")
        assert (media_root / stored.key).exists()

        storage.delete(stored.key)
        assert not (media_root / stored.key).exists()

    def test_delete_is_idempotent(self, db, media_root):
        get_storage().delete("generated/1/missing.png")

    def test_media_base_url_is_prefixed(self, db, settings, media_root):
        settings.MEDIA_BASE_URL = "https://api.example.com"
        stored = get_storage().save("generated/1/a.png", b"data", "image/png")
        assert stored.url.startswith("https://api.example.com/media/")

    def test_unknown_storage_raises(self, settings):
        settings.IMAGE_STORAGE = "s3"
        with pytest.raises(KeyError, match="Unknown IMAGE_STORAGE"):
            get_storage()


class TestGenerateImageService:
    def test_returns_a_saved_row(self, user, media_root):
        image = generate_image(
            user=user, prompt="a harbour at night", size="1536x1024", quality="hd"
        )
        assert image.pk
        assert image.duration_ms >= 0
        assert (image.width, image.height) == (1536, 1024)

    def test_orphan_file_is_removed_when_the_insert_fails(
        self, user, media_root, monkeypatch
    ):
        def boom(*args, **kwargs):
            raise DatabaseError("connection lost")

        monkeypatch.setattr(GeneratedImage.objects, "create", boom)
        with pytest.raises(StorageError):
            generate_image(
                user=user, prompt="a harbour", size="1024x1024", quality="standard"
            )
        assert not list(media_root.rglob("*.png"))
        assert GeneratedImage.objects.count() == 0
