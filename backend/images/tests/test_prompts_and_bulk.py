import pytest
from django.urls import reverse

from images.models import GeneratedImage, SavedPrompt

PROMPTS = reverse("images:saved-prompt-list")
BULK_DELETE = reverse("images:bulk-delete")
QUOTA = reverse("images:quota")
GENERATE = reverse("images:generate")


def prompt_detail(pk):
    return reverse("images:saved-prompt-detail", args=[pk])


def prompt_use(pk):
    return reverse("images:saved-prompt-use", args=[pk])


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


class TestSavedPrompts:
    def test_requires_authentication(self, client, db):
        assert client.get(PROMPTS).status_code == 401

    def test_saves_a_prompt(self, auth_client, user):
        response = auth_client.post(
            PROMPTS,
            {"prompt": "A snow leopard on a ridge", "size": "1024x1536", "quality": "hd"},
            format="json",
        )

        assert response.status_code == 201
        saved = SavedPrompt.objects.get(user=user)
        assert saved.prompt == "A snow leopard on a ridge"
        assert saved.size == "1024x1536"

    def test_trims_the_prompt(self, auth_client, user):
        auth_client.post(PROMPTS, {"prompt": "  a windmill at dawn  "}, format="json")
        assert SavedPrompt.objects.get(user=user).prompt == "a windmill at dawn"

    def test_falls_back_to_the_prompt_for_a_label(self, auth_client):
        response = auth_client.post(
            PROMPTS, {"prompt": "a copper teapot on linen"}, format="json"
        )
        assert response.data["display_label"] == "a copper teapot on linen"

    def test_uses_an_explicit_label_when_given(self, auth_client):
        response = auth_client.post(
            PROMPTS, {"prompt": "a copper teapot", "label": "Teapot"}, format="json"
        )
        assert response.data["display_label"] == "Teapot"

    def test_rejects_a_duplicate_with_a_field_error_not_a_500(self, auth_client):
        auth_client.post(PROMPTS, {"prompt": "a copper teapot"}, format="json")

        response = auth_client.post(PROMPTS, {"prompt": "a copper teapot"}, format="json")

        assert response.status_code == 400
        assert "prompt" in response.data

    def test_the_same_prompt_may_be_saved_by_two_accounts(
        self, auth_client, user, other_user
    ):
        SavedPrompt.objects.create(user=other_user, prompt="a shared idea")

        response = auth_client.post(PROMPTS, {"prompt": "a shared idea"}, format="json")

        assert response.status_code == 201

    def test_rejects_a_too_short_prompt(self, auth_client):
        response = auth_client.post(PROMPTS, {"prompt": "ab"}, format="json")
        assert response.status_code == 400

    def test_lists_only_the_callers_prompts(self, auth_client, user, other_user):
        SavedPrompt.objects.create(user=user, prompt="mine")
        SavedPrompt.objects.create(user=other_user, prompt="theirs")

        response = auth_client.get(PROMPTS)

        assert [row["prompt"] for row in response.data] == ["mine"]

    def test_is_not_paginated(self, auth_client, user):
        for index in range(20):
            SavedPrompt.objects.create(user=user, prompt=f"prompt {index}")

        response = auth_client.get(PROMPTS)

        assert isinstance(response.data, list)
        assert len(response.data) == 20

    def test_can_be_renamed(self, auth_client, user):
        saved = SavedPrompt.objects.create(user=user, prompt="a copper teapot")

        response = auth_client.patch(
            prompt_detail(saved.pk), {"label": "Teapot"}, format="json"
        )

        assert response.status_code == 200
        saved.refresh_from_db()
        assert saved.label == "Teapot"

    def test_can_be_deleted(self, auth_client, user):
        saved = SavedPrompt.objects.create(user=user, prompt="a copper teapot")

        assert auth_client.delete(prompt_detail(saved.pk)).status_code == 204
        assert not SavedPrompt.objects.filter(pk=saved.pk).exists()

    def test_another_users_prompt_is_not_found(self, auth_client, other_user):
        saved = SavedPrompt.objects.create(user=other_user, prompt="theirs")

        assert auth_client.get(prompt_detail(saved.pk)).status_code == 404
        assert auth_client.delete(prompt_detail(saved.pk)).status_code == 404
        assert SavedPrompt.objects.filter(pk=saved.pk).exists()

    def test_recording_use_increments_the_counter(self, auth_client, user):
        saved = SavedPrompt.objects.create(user=user, prompt="a copper teapot")

        response = auth_client.post(prompt_use(saved.pk))

        assert response.status_code == 200
        saved.refresh_from_db()
        assert saved.use_count == 1
        assert saved.last_used_at is not None

    def test_cannot_record_use_on_another_users_prompt(self, auth_client, other_user):
        saved = SavedPrompt.objects.create(user=other_user, prompt="theirs")

        assert auth_client.post(prompt_use(saved.pk)).status_code == 404
        saved.refresh_from_db()
        assert saved.use_count == 0

    def test_survives_deleting_the_image_it_came_from(self, auth_client, user):
        image = make_image(user, prompt="a copper teapot")
        auth_client.post(PROMPTS, {"prompt": "a copper teapot"}, format="json")

        auth_client.delete(reverse("images:detail", args=[image.pk]))

        assert SavedPrompt.objects.filter(user=user, prompt="a copper teapot").exists()


class TestBulkDelete:
    def test_requires_authentication(self, client, db):
        assert client.post(BULK_DELETE, {"ids": [1]}, format="json").status_code == 401

    def test_deletes_several_at_once(self, auth_client, user):
        images = [make_image(user, prompt=f"image {i}") for i in range(3)]

        response = auth_client.post(
            BULK_DELETE, {"ids": [i.pk for i in images]}, format="json"
        )

        assert response.status_code == 200
        assert response.data["deleted"] == 3
        assert GeneratedImage.objects.filter(user=user).count() == 0

    def test_removes_the_stored_files(self, auth_client, media_root):
        first = auth_client.post(GENERATE, {"prompt": "a red balloon"}, format="json")
        second = auth_client.post(GENERATE, {"prompt": "a blue balloon"}, format="json")
        assert len(list(media_root.rglob("*.png"))) == 2

        auth_client.post(
            BULK_DELETE,
            {"ids": [first.data["id"], second.data["id"]]},
            format="json",
        )

        assert not list(media_root.rglob("*.png"))

    def test_silently_ignores_another_users_ids(self, auth_client, user, other_user):
        mine = make_image(user, prompt="mine")
        theirs = make_image(other_user, prompt="theirs")

        response = auth_client.post(
            BULK_DELETE, {"ids": [mine.pk, theirs.pk]}, format="json"
        )

        assert response.status_code == 200
        assert response.data["deleted"] == 1
        assert response.data["requested"] == 2
        assert GeneratedImage.objects.filter(pk=theirs.pk).exists()

    def test_unknown_ids_are_counted_but_not_an_error(self, auth_client, user):
        image = make_image(user)

        response = auth_client.post(
            BULK_DELETE, {"ids": [image.pk, 999999]}, format="json"
        )

        assert response.status_code == 200
        assert response.data["deleted"] == 1

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"ids": []},
            {"ids": "not-a-list"},
            {"ids": ["abc"]},
            {"ids": [1.5]},
        ],
    )
    def test_rejects_a_malformed_body(self, auth_client, payload):
        response = auth_client.post(BULK_DELETE, payload, format="json")
        assert response.status_code == 400
        assert "ids" in response.data

    def test_caps_the_batch_size(self, auth_client):
        response = auth_client.post(
            BULK_DELETE, {"ids": list(range(1, 102))}, format="json"
        )
        assert response.status_code == 400


class TestQuota:
    def test_requires_authentication(self, client, db):
        assert client.get(QUOTA).status_code == 401

    def test_reports_the_configured_limit(self, auth_client):
        quota = auth_client.get(QUOTA).data["quota"]

        assert quota["limit"] > 0
        assert quota["remaining"] <= quota["limit"]
        assert quota["window_seconds"] > 0

    def test_reading_the_quota_does_not_consume_it(self, auth_client):
        first = auth_client.get(QUOTA).data["quota"]["remaining"]
        auth_client.get(QUOTA)
        second = auth_client.get(QUOTA).data["quota"]["remaining"]

        assert first == second

    def test_generating_consumes_one(self, auth_client):
        before = auth_client.get(QUOTA).data["quota"]["remaining"]

        auth_client.post(GENERATE, {"prompt": "a lighthouse"}, format="json")

        after = auth_client.get(QUOTA).data["quota"]["remaining"]
        assert after == before - 1

    def test_the_generate_response_carries_the_quota(self, auth_client):
        response = auth_client.post(GENERATE, {"prompt": "a lighthouse"}, format="json")

        assert response.status_code == 201
        assert response.data["quota"]["remaining"] >= 0
        assert response.data["image_url"]

    def test_each_account_has_its_own_allowance(self, client, user, other_user):
        client.force_authenticate(user=user)
        client.post(GENERATE, {"prompt": "a lighthouse"}, format="json")
        mine = client.get(QUOTA).data["quota"]

        client.force_authenticate(user=other_user)
        theirs = client.get(QUOTA).data["quota"]

        assert theirs["remaining"] > mine["remaining"]
