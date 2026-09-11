from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from images.constants import SUPPORTED_MODELS, default_model
from images.models import GeneratedImage, ShareLink

GENERATE = reverse("images:generate")
OPTIONS = reverse("images:options")


def share_url(pk):
    return reverse("images:share", args=[pk])


def revoke_url(pk):
    return reverse("images:share-revoke", args=[pk])


def shared_url(token):
    return reverse("images:shared-image", args=[token])


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


class TestCreatingAShareLink:
    def test_requires_authentication(self, client, db, user):
        image = make_image(user)
        assert client.post(share_url(image.pk)).status_code == 401

    def test_creates_a_link(self, auth_client, user):
        image = make_image(user)

        response = auth_client.post(share_url(image.pk), {}, format="json")

        assert response.status_code == 201
        assert response.data["token"]
        assert response.data["active"] is True
        assert response.data["url"].endswith(response.data["token"])

    def test_token_is_long_and_unguessable(self, auth_client, user):
        image = make_image(user)

        first = auth_client.post(share_url(image.pk), {}, format="json").data["token"]
        second_image = make_image(user, prompt="another")
        second = auth_client.post(share_url(second_image.pk), {}, format="json").data[
            "token"
        ]

        assert len(first) >= 40
        assert first != second

    def test_honours_a_custom_lifetime(self, auth_client, user):
        image = make_image(user)

        response = auth_client.post(
            share_url(image.pk), {"expires_in_hours": 24}, format="json"
        )

        expires = timezone.datetime.fromisoformat(
            response.data["expires_at"].replace("Z", "+00:00")
        )
        assert timedelta(hours=23) < (expires - timezone.now()) <= timedelta(hours=24)

    @pytest.mark.parametrize("hours", [0, -1, 721])
    def test_rejects_an_unreasonable_lifetime(self, auth_client, user, hours):
        image = make_image(user)
        response = auth_client.post(
            share_url(image.pk), {"expires_in_hours": hours}, format="json"
        )
        assert response.status_code == 400

    def test_cannot_share_another_users_image(self, auth_client, other_user):
        image = make_image(other_user)

        assert auth_client.post(share_url(image.pk), {}, format="json").status_code == 404
        assert ShareLink.objects.count() == 0

    def test_lists_the_links_for_an_image(self, auth_client, user):
        image = make_image(user)
        auth_client.post(share_url(image.pk), {}, format="json")

        response = auth_client.get(share_url(image.pk))

        assert response.status_code == 200
        assert len(response.data) == 1


class TestViewingASharedImage:
    def test_is_public(self, client, auth_client, user):
        image = make_image(user, prompt="a shared harbour")
        token = auth_client.post(share_url(image.pk), {}, format="json").data["token"]

        response = client.get(shared_url(token))

        assert response.status_code == 200
        assert response.data["prompt"] == "a shared harbour"

    def test_exposes_only_the_image_not_the_owner(self, client, auth_client, user):
        image = make_image(user)
        token = auth_client.post(share_url(image.pk), {}, format="json").data["token"]

        body = client.get(shared_url(token)).data

        assert set(body) == {
            "prompt",
            "image_url",
            "size",
            "width",
            "height",
            "created_at",
        }
        assert user.email not in str(body)

    def test_counts_views(self, client, auth_client, user):
        image = make_image(user)
        token = auth_client.post(share_url(image.pk), {}, format="json").data["token"]

        client.get(shared_url(token))
        client.get(shared_url(token))

        assert ShareLink.objects.get(token=token).view_count == 2

    def test_an_unknown_token_is_a_404(self, client, db):
        assert client.get(shared_url("no-such-token")).status_code == 404


class TestRevocationAndExpiry:
    def test_a_revoked_link_stops_working(self, client, auth_client, user):
        image = make_image(user)
        created = auth_client.post(share_url(image.pk), {}, format="json").data
        assert client.get(shared_url(created["token"])).status_code == 200

        auth_client.delete(revoke_url(created["id"]))

        assert client.get(shared_url(created["token"])).status_code == 404

    def test_an_expired_link_stops_working(self, client, auth_client, user):
        image = make_image(user)
        token = auth_client.post(share_url(image.pk), {}, format="json").data["token"]

        link = ShareLink.objects.get(token=token)
        link.expires_at = timezone.now() - timedelta(seconds=1)
        link.save(update_fields=["expires_at"])

        assert client.get(shared_url(token)).status_code == 404

    def test_dead_and_never_existed_are_indistinguishable(
        self, client, auth_client, user
    ):
        image = make_image(user)
        created = auth_client.post(share_url(image.pk), {}, format="json").data
        auth_client.delete(revoke_url(created["id"]))

        revoked = client.get(shared_url(created["token"]))
        never = client.get(shared_url("token-that-never-existed"))

        assert revoked.status_code == never.status_code == 404
        assert str(revoked.data) == str(never.data)

    def test_cannot_revoke_another_users_link(self, auth_client, other_user, client):
        image = make_image(other_user)
        link = ShareLink.objects.create(
            image=image,
            token=ShareLink.new_token(),
            expires_at=timezone.now() + timedelta(days=1),
        )

        assert auth_client.delete(revoke_url(link.pk)).status_code == 404
        link.refresh_from_db()
        assert link.revoked_at is None

    def test_deleting_the_image_removes_its_links(self, auth_client, user, client):
        image = make_image(user)
        token = auth_client.post(share_url(image.pk), {}, format="json").data["token"]

        auth_client.delete(reverse("images:detail", args=[image.pk]))

        assert not ShareLink.objects.filter(token=token).exists()
        assert client.get(shared_url(token)).status_code == 404

    def test_revoking_twice_is_harmless(self, auth_client, user):
        image = make_image(user)
        created = auth_client.post(share_url(image.pk), {}, format="json").data

        auth_client.delete(revoke_url(created["id"]))
        first = ShareLink.objects.get(pk=created["id"]).revoked_at
        auth_client.delete(revoke_url(created["id"]))

        assert ShareLink.objects.get(pk=created["id"]).revoked_at == first


class TestModelCatalogue:
    def test_options_lists_the_models(self, client, db):
        response = client.get(OPTIONS)

        assert response.status_code == 200
        values = [entry["value"] for entry in response.data["models"]]
        assert values == list(SUPPORTED_MODELS)

    def test_exactly_one_model_is_the_default(self, client, db):
        defaults = [e for e in client.get(OPTIONS).data["models"] if e["default"]]
        assert len(defaults) == 1
        assert defaults[0]["value"] == default_model()

    def test_a_catalogue_model_is_accepted(self, auth_client):
        response = auth_client.post(
            GENERATE,
            {"prompt": "a lighthouse", "model": SUPPORTED_MODELS[1]},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["model"] == SUPPORTED_MODELS[1]

    def test_an_unlisted_model_is_rejected(self, auth_client):
        response = auth_client.post(
            GENERATE,
            {"prompt": "a lighthouse", "model": "somebody/private-model"},
            format="json",
        )

        assert response.status_code == 400
        assert "model" in response.data
        assert GeneratedImage.objects.count() == 0

    def test_omitting_the_model_uses_the_server_default(self, auth_client):
        response = auth_client.post(GENERATE, {"prompt": "a lighthouse"}, format="json")

        assert response.status_code == 201
        assert response.data["model"] == "stub/gradient"
