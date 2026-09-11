import re

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = "correct-horse-battery"
NEW_PASSWORD = "a-brand-new-passphrase"

REQUEST = reverse("accounts:password-reset")
CONFIRM = reverse("accounts:password-reset-confirm")
VERIFY = reverse("accounts:email-verify")
VERIFY_REQUEST = reverse("accounts:email-verify-request")


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="painter@example.com", password=PASSWORD, display_name="Painter"
    )


def link_parts(message):
    match = re.search(r"[?&]uid=([^&\s]+)&token=([^\s&]+)", message.body)
    assert match, f"no link found in:\n{message.body}"
    return {"uid": match.group(1), "token": match.group(2)}


def request_reset(client, email="painter@example.com"):
    mail.outbox.clear()
    response = client.post(REQUEST, {"email": email}, format="json")
    return response


class TestRequestDoesNotLeakAccountExistence:
    def test_known_address_is_accepted(self, client, user):
        assert request_reset(client).status_code == 202

    def test_unknown_address_is_also_accepted(self, client, db):
        assert request_reset(client, "nobody@example.com").status_code == 202

    def test_both_responses_are_byte_identical(self, client, user):
        known = request_reset(client)
        unknown = request_reset(client, "nobody@example.com")
        assert known.status_code == unknown.status_code
        assert known.data == unknown.data

    def test_only_the_real_address_receives_mail(self, client, user):
        request_reset(client)
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["painter@example.com"]

        request_reset(client, "nobody@example.com")
        assert len(mail.outbox) == 0

    def test_an_inactive_account_gets_no_mail_but_the_same_answer(self, client, user):
        user.is_active = False
        user.save()

        response = request_reset(client)

        assert response.status_code == 202
        assert len(mail.outbox) == 0

    def test_a_send_failure_still_returns_the_neutral_response(
        self, client, user, monkeypatch
    ):

        def explode(*args, **kwargs):
            raise OSError("smtp unreachable")

        monkeypatch.setattr("accounts.emails.send_mail", explode)

        response = client.post(REQUEST, {"email": user.email}, format="json")

        assert response.status_code == 202
        assert "an account exists" in response.data["detail"].lower()

    def test_email_is_case_and_space_insensitive(self, client, user):
        mail.outbox.clear()
        client.post(REQUEST, {"email": "  PAINTER@Example.COM  "}, format="json")
        assert len(mail.outbox) == 1


class TestResetEmail:
    def test_contains_a_usable_link(self, client, user):
        request_reset(client)
        parts = link_parts(mail.outbox[0])
        assert parts["uid"] and parts["token"]

    def test_link_points_at_the_frontend_not_the_api(self, client, user):
        request_reset(client)
        assert settings.FRONTEND_BASE_URL in mail.outbox[0].body
        assert "/reset-password" in mail.outbox[0].body

    def test_never_contains_the_password_hash(self, client, user):
        request_reset(client)
        assert user.password not in mail.outbox[0].body


class TestConfirm:
    def test_sets_the_new_password(self, client, user):
        request_reset(client)
        payload = {**link_parts(mail.outbox[0]), "new_password": NEW_PASSWORD}

        response = client.post(CONFIRM, payload, format="json")

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
        assert not user.check_password(PASSWORD)

    def test_signs_the_user_in(self, client, user):
        request_reset(client)
        payload = {**link_parts(mail.outbox[0]), "new_password": NEW_PASSWORD}

        response = client.post(CONFIRM, payload, format="json")

        assert response.data["access"]
        assert response.data["user"]["email"] == user.email
        assert settings.AUTH_COOKIE_REFRESH in response.cookies

    def test_the_token_works_only_once(self, client, user):
        request_reset(client)
        payload = {**link_parts(mail.outbox[0]), "new_password": NEW_PASSWORD}
        assert client.post(CONFIRM, payload, format="json").status_code == 200

        replay = client.post(
            CONFIRM, {**payload, "new_password": "yet-another-password"}, format="json"
        )

        assert replay.status_code == 400
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    def test_rejects_a_tampered_token(self, client, user):
        request_reset(client)
        parts = link_parts(mail.outbox[0])
        parts["token"] = parts["token"][:-1] + ("a" if parts["token"][-1] != "a" else "b")

        response = client.post(
            CONFIRM, {**parts, "new_password": NEW_PASSWORD}, format="json"
        )

        assert response.status_code == 400
        user.refresh_from_db()
        assert user.check_password(PASSWORD)

    def test_rejects_a_malformed_uid(self, client, user):
        request_reset(client)
        parts = link_parts(mail.outbox[0])

        response = client.post(
            CONFIRM,
            {**parts, "uid": "!!!not-base64!!!", "new_password": NEW_PASSWORD},
            format="json",
        )

        assert response.status_code == 400

    def test_a_token_cannot_be_redeemed_against_another_account(self, client, user, db):
        victim = User.objects.create_user(email="victim@example.com", password=PASSWORD)
        request_reset(client)
        parts = link_parts(mail.outbox[0])

        from accounts.tokens import encode_uid

        response = client.post(
            CONFIRM,
            {**parts, "uid": encode_uid(victim), "new_password": NEW_PASSWORD},
            format="json",
        )

        assert response.status_code == 400
        victim.refresh_from_db()
        assert victim.check_password(PASSWORD)

    def test_enforces_password_validators(self, client, user):
        request_reset(client)
        payload = {**link_parts(mail.outbox[0]), "new_password": "123"}

        response = client.post(CONFIRM, payload, format="json")

        assert response.status_code == 400
        assert "new_password" in response.data

    def test_every_failure_gives_the_same_message(self, client, user):
        request_reset(client)
        parts = link_parts(mail.outbox[0])

        tampered = client.post(
            CONFIRM,
            {**parts, "token": "abc-invalidtoken", "new_password": NEW_PASSWORD},
            format="json",
        )
        unknown = client.post(
            CONFIRM,
            {"uid": "OTk5OTk5", "token": parts["token"], "new_password": NEW_PASSWORD},
            format="json",
        )

        assert str(tampered.data) == str(unknown.data)


class TestSessionEviction:
    def test_existing_refresh_tokens_stop_working(self, client, user):
        attacker = APIClient()
        attacker.post(
            reverse("accounts:login"),
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        allowed_origin = settings.CORS_ALLOWED_ORIGINS[0]
        assert (
            attacker.post(
                reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin
            ).status_code
            == 200
        )

        request_reset(client)
        payload = {**link_parts(mail.outbox[0]), "new_password": NEW_PASSWORD}
        client.post(CONFIRM, payload, format="json")

        assert (
            attacker.post(
                reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin
            ).status_code
            == 401
        )


class TestEmailVerification:
    def test_registration_sends_a_confirmation(self, client, db):
        mail.outbox.clear()
        client.post(
            reverse("accounts:register"),
            {"email": "new@example.com", "password": PASSWORD},
            format="json",
        )
        assert len(mail.outbox) == 1
        assert "/verify-email" in mail.outbox[0].body

    def test_a_new_account_starts_unverified(self, client, db):
        response = client.post(
            reverse("accounts:register"),
            {"email": "new@example.com", "password": PASSWORD},
            format="json",
        )
        assert response.data["user"]["email_verified"] is False

    def test_registration_succeeds_even_if_the_email_fails(self, client, db, monkeypatch):

        def explode(*args, **kwargs):
            raise OSError("smtp unreachable")

        monkeypatch.setattr("accounts.emails.send_mail", explode)

        response = client.post(
            reverse("accounts:register"),
            {"email": "new@example.com", "password": PASSWORD},
            format="json",
        )

        assert response.status_code == 201
        assert User.objects.filter(email="new@example.com").exists()

    def test_an_unverified_user_can_still_sign_in_and_generate(self, client, user):
        response = client.post(
            reverse("accounts:login"),
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        assert response.status_code == 200

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        generate = client.post(
            reverse("images:generate"), {"prompt": "a harbour"}, format="json"
        )
        assert generate.status_code == 201

    def test_the_link_verifies_the_address(self, client, db):
        mail.outbox.clear()
        client.post(
            reverse("accounts:register"),
            {"email": "new@example.com", "password": PASSWORD},
            format="json",
        )
        parts = link_parts(mail.outbox[0])

        response = client.post(VERIFY, parts, format="json")

        assert response.status_code == 200
        assert response.data["user"]["email_verified"] is True
        assert User.objects.get(email="new@example.com").is_email_verified

    def test_verifying_twice_is_harmless(self, client, db):
        mail.outbox.clear()
        client.post(
            reverse("accounts:register"),
            {"email": "new@example.com", "password": PASSWORD},
            format="json",
        )
        parts = link_parts(mail.outbox[0])
        client.post(VERIFY, parts, format="json")
        first = User.objects.get(email="new@example.com").email_verified_at

        client.post(VERIFY, parts, format="json")

        assert User.objects.get(email="new@example.com").email_verified_at == first

    def test_rejects_a_tampered_token(self, client, db):
        mail.outbox.clear()
        client.post(
            reverse("accounts:register"),
            {"email": "new@example.com", "password": PASSWORD},
            format="json",
        )
        parts = link_parts(mail.outbox[0])
        parts["token"] = "not-a-real-token"

        assert client.post(VERIFY, parts, format="json").status_code == 400
        assert not User.objects.get(email="new@example.com").is_email_verified

    def test_a_password_change_does_not_invalidate_a_pending_link(self, client, db):
        mail.outbox.clear()
        register = client.post(
            reverse("accounts:register"),
            {"email": "new@example.com", "password": PASSWORD},
            format="json",
        )
        parts = link_parts(mail.outbox[0])

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {register.data['access']}")
        client.post(
            reverse("accounts:change-password"),
            {"current_password": PASSWORD, "new_password": NEW_PASSWORD},
            format="json",
        )
        client.credentials()

        assert client.post(VERIFY, parts, format="json").status_code == 200

    def test_resend_requires_authentication(self, client, db):
        assert client.post(VERIFY_REQUEST).status_code == 401

    def test_resend_sends_a_fresh_link(self, client, user):
        login = client.post(
            reverse("accounts:login"),
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        mail.outbox.clear()

        response = client.post(VERIFY_REQUEST)

        assert response.status_code == 202
        assert len(mail.outbox) == 1

    def test_resend_is_a_no_op_once_verified(self, client, user):
        user.mark_email_verified()
        login = client.post(
            reverse("accounts:login"),
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        mail.outbox.clear()

        response = client.post(VERIFY_REQUEST)

        assert response.status_code == 200
        assert "already confirmed" in response.data["detail"].lower()
        assert len(mail.outbox) == 0
