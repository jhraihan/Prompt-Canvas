import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = "correct-horse-battery"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="painter@example.com", password=PASSWORD, display_name="Painter"
    )


@pytest.fixture
def allowed_origin():
    return settings.CORS_ALLOWED_ORIGINS[0]


def login(client, email=None, password=PASSWORD):
    return client.post(
        reverse("accounts:login"),
        {"email": email or "painter@example.com", "password": password},
        format="json",
    )


class TestRegister:
    def test_creates_user_and_returns_access_token(self, client, db):
        response = client.post(
            reverse("accounts:register"),
            {"email": "New@Example.com", "password": PASSWORD, "display_name": "New"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["user"]["email"] == "new@example.com"
        assert response.data["access"]
        assert User.objects.filter(email="new@example.com").exists()

    def test_refresh_token_is_never_in_the_body(self, client, db):
        response = client.post(
            reverse("accounts:register"),
            {"email": "a@example.com", "password": PASSWORD},
            format="json",
        )
        assert "refresh" not in response.data

    def test_refresh_cookie_is_httponly(self, client, db):
        response = client.post(
            reverse("accounts:register"),
            {"email": "b@example.com", "password": PASSWORD},
            format="json",
        )
        cookie = response.cookies[settings.AUTH_COOKIE_REFRESH]
        assert cookie["httponly"] is True
        assert cookie["path"] == settings.AUTH_COOKIE_PATH

    def test_rejects_duplicate_email(self, client, user):
        response = client.post(
            reverse("accounts:register"),
            {"email": "painter@example.com", "password": PASSWORD},
            format="json",
        )
        assert response.status_code == 400
        assert "email" in response.data

    def test_rejects_weak_password(self, client, db):
        response = client.post(
            reverse("accounts:register"),
            {"email": "weak@example.com", "password": "12345"},
            format="json",
        )
        assert response.status_code == 400
        assert "password" in response.data


class TestLogin:
    def test_valid_credentials(self, client, user):
        response = login(client)
        assert response.status_code == 200
        assert response.data["access"]
        assert settings.AUTH_COOKIE_REFRESH in response.cookies

    def test_wrong_password(self, client, user):
        response = login(client, password="not-the-password")
        assert response.status_code == 401
        assert settings.AUTH_COOKIE_REFRESH not in response.cookies

    def test_inactive_user_cannot_log_in(self, client, user):
        user.is_active = False
        user.save()
        assert login(client).status_code == 401


class TestRefresh:
    def test_cookie_is_exchanged_for_a_new_access_token(
        self, client, user, allowed_origin
    ):
        login(client)
        response = client.post(reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin)
        assert response.status_code == 200
        assert response.data["access"]
        assert response.data["user"]["email"] == user.email

    def test_cookie_is_rotated(self, client, user, allowed_origin):
        first = login(client).cookies[settings.AUTH_COOKIE_REFRESH].value
        response = client.post(reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin)
        assert response.cookies[settings.AUTH_COOKIE_REFRESH].value != first

    def test_rotated_token_cannot_be_replayed(self, client, user, allowed_origin):
        stale = login(client).cookies[settings.AUTH_COOKIE_REFRESH].value
        client.post(reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin)
        client.cookies[settings.AUTH_COOKIE_REFRESH] = stale
        replay = client.post(reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin)
        assert replay.status_code == 401

    def test_without_cookie_is_unauthorised(self, client, db, allowed_origin):
        response = client.post(reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin)
        assert response.status_code == 401

    def test_untrusted_origin_is_rejected(self, client, user):
        login(client)
        response = client.post(
            reverse("accounts:refresh"), HTTP_ORIGIN="https://evil.example.com"
        )
        assert response.status_code == 403

    def test_untrusted_referer_is_rejected(self, client, user):
        login(client)
        response = client.post(
            reverse("accounts:refresh"), HTTP_REFERER="https://evil.example.com/attack"
        )
        assert response.status_code == 403


class TestLogout:
    def test_clears_cookie_and_blacklists_token(self, client, user, allowed_origin):
        login(client)
        response = client.post(reverse("accounts:logout"), HTTP_ORIGIN=allowed_origin)
        assert response.status_code == 204
        assert response.cookies[settings.AUTH_COOKIE_REFRESH].value == ""

        refresh = client.post(reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin)
        assert refresh.status_code == 401

    def test_untrusted_origin_is_rejected(self, client, user):
        login(client)
        response = client.post(
            reverse("accounts:logout"), HTTP_ORIGIN="https://evil.example.com"
        )
        assert response.status_code == 403


class TestProfile:
    def test_me_requires_authentication(self, client, db):
        assert client.get(reverse("accounts:me")).status_code == 401

    def test_me_returns_the_current_user(self, client, user):
        access = login(client).data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.get(reverse("accounts:me"))
        assert response.status_code == 200
        assert response.data["email"] == user.email

    def test_display_name_can_be_updated(self, client, user):
        access = login(client).data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.patch(
            reverse("accounts:me"), {"display_name": "Renamed"}, format="json"
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.display_name == "Renamed"

    def test_email_is_read_only(self, client, user):
        access = login(client).data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        client.patch(
            reverse("accounts:me"), {"email": "hijack@example.com"}, format="json"
        )
        user.refresh_from_db()
        assert user.email == "painter@example.com"


class TestChangePassword:
    def test_password_is_changed_and_session_renewed(self, client, user):
        access = login(client).data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.post(
            reverse("accounts:change-password"),
            {"current_password": PASSWORD, "new_password": "a-brand-new-secret"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["access"]
        user.refresh_from_db()
        assert user.check_password("a-brand-new-secret")

    def test_wrong_current_password_is_rejected(self, client, user):
        access = login(client).data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.post(
            reverse("accounts:change-password"),
            {"current_password": "wrong", "new_password": "a-brand-new-secret"},
            format="json",
        )
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.check_password(PASSWORD)


class TestThrottleScopes:
    @pytest.fixture(autouse=True)
    def _rates(self, monkeypatch):
        from django.core.cache import cache
        from rest_framework.throttling import SimpleRateThrottle

        def apply(**rates):
            merged = {**SimpleRateThrottle.THROTTLE_RATES, **rates}
            monkeypatch.setattr(
                SimpleRateThrottle, "THROTTLE_RATES", merged, raising=False
            )
            cache.clear()

        cache.clear()
        return apply

    def test_login_has_its_own_budget(self, client, user, _rates):
        _rates(login="3/hour")

        for _ in range(3):
            assert login(client, password="wrong").status_code == 401
        assert login(client, password="wrong").status_code == 429

    def test_exhausting_login_does_not_block_registration(self, client, user, _rates):
        _rates(login="2/hour", register="10/hour")

        for _ in range(3):
            login(client, password="wrong")
        assert login(client, password="wrong").status_code == 429

        response = client.post(
            reverse("accounts:register"),
            {"email": "fresh@example.com", "password": PASSWORD},
            format="json",
        )
        assert response.status_code == 201

    def test_register_has_its_own_budget(self, client, db, _rates):
        _rates(register="2/hour")

        for index in range(2):
            response = client.post(
                reverse("accounts:register"),
                {"email": f"user{index}@example.com", "password": PASSWORD},
                format="json",
            )
            assert response.status_code == 201

        response = client.post(
            reverse("accounts:register"),
            {"email": "blocked@example.com", "password": PASSWORD},
            format="json",
        )
        assert response.status_code == 429

    def test_refresh_is_throttled(self, client, user, allowed_origin, _rates):
        _rates(token="3/hour")
        login(client)

        seen_429 = False
        for _ in range(5):
            response = client.post(
                reverse("accounts:refresh"), HTTP_ORIGIN=allowed_origin
            )
            if response.status_code == 429:
                seen_429 = True
                break
        assert seen_429, "refresh must be rate limited"

    def test_logout_is_throttled(self, client, user, allowed_origin, _rates):
        _rates(token="2/hour")
        login(client)

        seen_429 = False
        for _ in range(5):
            response = client.post(reverse("accounts:logout"), HTTP_ORIGIN=allowed_origin)
            if response.status_code == 429:
                seen_429 = True
                break
        assert seen_429, "logout must be rate limited"
