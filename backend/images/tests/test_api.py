import pytest
from django.urls import reverse

from images.exceptions import (
    ProviderAuthError,
    ProviderRateLimited,
    ProviderRejectedPrompt,
    ProviderTimeout,
)
from images.models import GeneratedImage

GENERATE = reverse("images:generate")
LIST = reverse("images:list")


def detail(pk):
    return reverse("images:detail", args=[pk])


def make_image(user, **overrides):
    defaults = {
        "user": user,
        "prompt": "A futuristic city at sunset",
        "image_url": "http://testserver/media/generated/x.png",
        "storage_key": "generated/x.png",
        "size": "1024x1024",
        "quality": "standard",
        "provider": "stub",
        "model": "stub/gradient",
        "width": 1024,
        "height": 1024,
    }
    return GeneratedImage.objects.create(**{**defaults, **overrides})


class TestGenerate:
    def test_requires_authentication(self, client, db):
        response = client.post(GENERATE, {"prompt": "a cat"}, format="json")
        assert response.status_code == 401

    def test_creates_and_returns_an_image(self, auth_client, user):
        response = auth_client.post(
            GENERATE,
            {
                "prompt": "A futuristic city at sunset",
                "size": "1024x1024",
                "quality": "standard",
            },
            format="json",
        )
        assert response.status_code == 201
        body = response.data
        assert body["prompt"] == "A futuristic city at sunset"
        assert body["image_url"]
        assert body["size"] == "1024x1024"
        assert body["provider"] == "stub"
        assert body["download_filename"].startswith(
            "promptcanvas-a-futuristic-city-at-sunset"
        )
        assert GeneratedImage.objects.filter(user=user, pk=body["id"]).exists()

    def test_persists_metadata(self, auth_client, user):
        auth_client.post(
            GENERATE,
            {"prompt": "Portrait of a fox", "size": "1024x1536", "quality": "hd"},
            format="json",
        )
        image = GeneratedImage.objects.get(user=user)
        assert (image.width, image.height) == (1024, 1536)
        assert image.quality == "hd"
        assert image.byte_size > 0
        assert image.storage_key.startswith(f"generated/{user.pk}/")

    def test_writes_bytes_to_storage(self, auth_client, media_root):
        auth_client.post(GENERATE, {"prompt": "a lighthouse"}, format="json")
        written = list(media_root.rglob("*.png"))
        assert len(written) == 1
        assert written[0].read_bytes().startswith(b"\x89PNG")

    def test_defaults_size_and_quality(self, auth_client):
        response = auth_client.post(GENERATE, {"prompt": "a quiet lake"}, format="json")
        assert response.data["size"] == "1024x1024"
        assert response.data["quality"] == "standard"

    @pytest.mark.parametrize(
        "payload,field",
        [
            ({}, "prompt"),
            ({"prompt": ""}, "prompt"),
            ({"prompt": "   "}, "prompt"),
            ({"prompt": "ab"}, "prompt"),
            ({"prompt": "x" * 1001}, "prompt"),
            ({"prompt": "valid prompt", "size": "4096x4096"}, "size"),
            ({"prompt": "valid prompt", "quality": "ultra"}, "quality"),
        ],
    )
    def test_rejects_invalid_input(self, auth_client, payload, field):
        response = auth_client.post(GENERATE, payload, format="json")
        assert response.status_code == 400
        assert field in response.data

    def test_nothing_is_saved_when_validation_fails(self, auth_client):
        auth_client.post(GENERATE, {"prompt": ""}, format="json")
        assert GeneratedImage.objects.count() == 0

    def test_prompt_is_trimmed(self, auth_client):
        response = auth_client.post(
            GENERATE, {"prompt": "  a windmill at dawn  "}, format="json"
        )
        assert response.data["prompt"] == "a windmill at dawn"


class TestProviderFailures:
    @pytest.mark.parametrize(
        "error,status,code",
        [
            (ProviderRateLimited, 429, "rate_limited"),
            (ProviderTimeout, 504, "timeout"),
            (ProviderAuthError, 503, "provider_unconfigured"),
            (ProviderRejectedPrompt, 400, "prompt_rejected"),
        ],
    )
    def test_error_is_translated(self, auth_client, monkeypatch, error, status, code):
        def boom(*args, **kwargs):
            raise error("raw provider detail with hf_secrettoken inside")

        monkeypatch.setattr("images.views.generate_image", boom)
        response = auth_client.post(GENERATE, {"prompt": "a cat"}, format="json")

        assert response.status_code == status
        assert response.data["code"] == code
        assert "hf_secrettoken" not in str(response.data)

    def test_failure_saves_nothing(self, auth_client, monkeypatch):
        def boom(*args, **kwargs):
            raise ProviderTimeout("upstream stalled")

        monkeypatch.setattr("images.views.generate_image", boom)
        auth_client.post(GENERATE, {"prompt": "a cat"}, format="json")
        assert GeneratedImage.objects.count() == 0


class TestHistory:
    def test_requires_authentication(self, client, db):
        assert client.get(LIST).status_code == 401

    def test_lists_only_the_callers_images(self, auth_client, user, other_user):
        make_image(user, prompt="mine")
        make_image(other_user, prompt="theirs")
        response = auth_client.get(LIST)
        assert response.status_code == 200
        assert [row["prompt"] for row in response.data["results"]] == ["mine"]

    def test_newest_first(self, auth_client, user):
        first = make_image(user, prompt="older")
        second = make_image(user, prompt="newer")
        results = auth_client.get(LIST).data["results"]
        assert [r["id"] for r in results] == [second.pk, first.pk]

    def test_is_paginated(self, auth_client, user):
        for index in range(15):
            make_image(user, prompt=f"image {index}")
        response = auth_client.get(LIST)
        assert response.data["count"] == 15
        assert len(response.data["results"]) == 12
        assert response.data["next"]

    def test_page_size_is_capped(self, auth_client, user):
        make_image(user)
        response = auth_client.get(LIST, {"page_size": 500})
        assert response.status_code == 200


class TestDetailAndDelete:
    def test_detail_returns_own_image(self, auth_client, user):
        image = make_image(user)
        response = auth_client.get(detail(image.pk))
        assert response.status_code == 200
        assert response.data["id"] == image.pk

    def test_another_users_image_is_not_found(self, auth_client, other_user):
        image = make_image(other_user)
        assert auth_client.get(detail(image.pk)).status_code == 404

    def test_delete_removes_the_row(self, auth_client, user):
        image = make_image(user)
        response = auth_client.delete(detail(image.pk))
        assert response.status_code == 204
        assert not GeneratedImage.objects.filter(pk=image.pk).exists()

    def test_delete_removes_the_stored_file(self, auth_client, media_root):
        created = auth_client.post(GENERATE, {"prompt": "a red balloon"}, format="json")
        assert list(media_root.rglob("*.png"))
        auth_client.delete(detail(created.data["id"]))
        assert not list(media_root.rglob("*.png"))

    def test_cannot_delete_another_users_image(self, auth_client, other_user):
        image = make_image(other_user)
        assert auth_client.delete(detail(image.pk)).status_code == 404
        assert GeneratedImage.objects.filter(pk=image.pk).exists()


class TestOptions:
    def test_lists_supported_sizes_and_qualities(self, client, db):
        response = client.get(reverse("images:options"))
        assert response.status_code == 200
        assert [s["value"] for s in response.data["sizes"]] == [
            "1024x1024",
            "1024x1536",
            "1536x1024",
        ]
        assert [q["value"] for q in response.data["qualities"]] == ["standard", "hd"]

    def test_never_exposes_the_token(self, client, db, settings):
        settings.HF_TOKEN = "hf_supersecret"
        body = str(client.get(reverse("images:options")).data)
        assert "hf_supersecret" not in body


class TestHealth:
    def test_is_public(self, client, db):
        response = client.get(reverse("health"))
        assert response.status_code == 200
        assert response.data["status"] == "ok"


class TestProviderVisibility:
    def test_health_reports_the_active_provider(self, client, db):
        response = client.get(reverse("health"))
        assert response.status_code == 200
        assert response.data["status"] == "ok"
        assert response.data["provider"] == "stub"
        assert response.data["model"] == "stub/gradient"

    def test_health_flags_the_stub_as_degraded(self, client, db):
        assert client.get(reverse("health")).data["degraded"] is True

    def test_health_is_not_degraded_on_a_real_provider(self, client, db, settings):
        settings.IMAGE_PROVIDER = "huggingface"
        settings.HF_TOKEN = "hf_test_token"
        body = client.get(reverse("health")).data
        assert body["provider"] == "huggingface"
        assert body["degraded"] is False

    def test_health_never_exposes_the_token(self, client, db, settings):
        settings.IMAGE_PROVIDER = "huggingface"
        settings.HF_TOKEN = "hf_supersecret_value"
        assert "hf_supersecret_value" not in str(client.get(reverse("health")).data)

    def test_health_survives_an_unconfigured_provider(self, client, db, settings):
        settings.IMAGE_PROVIDER = "huggingface"
        settings.HF_TOKEN = ""
        response = client.get(reverse("health"))
        assert response.status_code == 200
        assert response.data["provider"] is None
        assert response.data["degraded"] is True


class TestDeploymentChecks:
    @staticmethod
    def _run(settings):
        from images.checks import check_image_provider

        return check_image_provider(None)

    def test_stub_is_allowed_when_debug_is_on(self, settings):
        settings.DEBUG = True
        settings.IMAGE_PROVIDER = "stub"
        assert self._run(settings) == []

    def test_a_declared_non_production_environment_is_exempt(self, settings):
        settings.DEBUG = False
        settings.IS_NON_PRODUCTION = True
        settings.IMAGE_PROVIDER = "stub"
        assert self._run(settings) == []

    def test_stub_is_an_error_when_debug_is_off(self, settings):
        settings.DEBUG = False
        settings.IS_NON_PRODUCTION = False
        settings.IMAGE_PROVIDER = "stub"
        problems = self._run(settings)
        assert [p.id for p in problems] == ["images.E001"]

    def test_unknown_provider_is_an_error(self, settings):
        settings.IMAGE_PROVIDER = "midjourney"
        assert [p.id for p in self._run(settings)] == ["images.E002"]

    def test_missing_token_is_a_warning(self, settings):
        settings.DEBUG = False
        settings.IS_NON_PRODUCTION = False
        settings.IMAGE_PROVIDER = "huggingface"
        settings.HF_TOKEN = ""
        assert [p.id for p in self._run(settings)] == ["images.W001"]

    def test_a_correct_production_setup_is_clean(self, settings):
        settings.DEBUG = False
        settings.IS_NON_PRODUCTION = False
        settings.IMAGE_PROVIDER = "huggingface"
        settings.HF_TOKEN = "hf_test_token"
        assert self._run(settings) == []
