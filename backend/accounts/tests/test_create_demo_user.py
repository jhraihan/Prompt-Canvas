import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

User = get_user_model()
PASSWORD = "demo-password-123"


def run(**options):
    out = io.StringIO()
    options.setdefault("email", "demo@example.com")
    options.setdefault("password", PASSWORD)
    call_command("create_demo_user", stdout=out, **options)
    return out.getvalue()


class TestCreate:
    def test_creates_the_account(self, db):
        output = run()

        user = User.objects.get(email="demo@example.com")
        assert user.check_password(PASSWORD)
        assert user.is_active
        assert "Created" in output

    def test_normalises_the_email(self, db):
        run(email="  Demo@EXAMPLE.com  ")
        assert User.objects.filter(email="demo@example.com").exists()

    def test_sets_the_display_name(self, db):
        run(display_name="Guest")
        assert User.objects.get(email="demo@example.com").display_name == "Guest"

    def test_defaults_the_display_name(self, db):
        run()
        assert User.objects.get(email="demo@example.com").display_name == "Demo"


class TestPrivileges:
    def test_a_new_demo_account_is_not_staff_or_superuser(self, db):
        run()
        user = User.objects.get(email="demo@example.com")
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_an_existing_superuser_is_demoted(self, db):
        User.objects.create_superuser(email="demo@example.com", password="x" * 12)

        run()

        user = User.objects.get(email="demo@example.com")
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_a_disabled_account_is_reactivated(self, db):
        user = User.objects.create_user(email="demo@example.com", password="x" * 12)
        user.is_active = False
        user.save()

        run()

        user.refresh_from_db()
        assert user.is_active is True


class TestIdempotence:
    def test_re_running_resets_rather_than_duplicating(self, db):
        run()
        output = run(password="a-different-password")

        assert User.objects.filter(email="demo@example.com").count() == 1
        assert "Reset" in output
        assert User.objects.get(email="demo@example.com").check_password(
            "a-different-password"
        )


class TestValidation:
    def test_rejects_a_short_password(self, db):
        with pytest.raises(CommandError, match="at least 8 characters"):
            run(password="short")

    def test_nothing_is_created_when_validation_fails(self, db):
        with pytest.raises(CommandError):
            run(password="short")
        assert not User.objects.filter(email="demo@example.com").exists()


class TestClearHistory:
    def test_deletes_the_demo_accounts_images(self, db, media_root):
        from images.services.generation import generate_image

        run()
        user = User.objects.get(email="demo@example.com")
        generate_image(
            user=user, prompt="a demo image", size="1024x1024", quality="standard"
        )
        assert user.images.count() == 1

        output = run(clear_history=True)

        assert user.images.count() == 0
        assert "Cleared 1 demo image(s)" in output

    def test_leaves_images_alone_by_default(self, db, media_root):
        from images.services.generation import generate_image

        run()
        user = User.objects.get(email="demo@example.com")
        generate_image(
            user=user, prompt="a demo image", size="1024x1024", quality="standard"
        )

        run()

        assert user.images.count() == 1

    def test_removes_the_stored_files_too(self, db, media_root):
        from images.services.generation import generate_image

        run()
        user = User.objects.get(email="demo@example.com")
        generate_image(
            user=user, prompt="a demo image", size="1024x1024", quality="standard"
        )
        assert list(media_root.rglob("*.png"))

        run(clear_history=True)

        assert not list(media_root.rglob("*.png"))


class TestOutput:
    def test_reminds_the_operator_to_sync_the_frontend(self, db):
        assert "VITE_DEMO_EMAIL" in run()

    def test_never_prints_the_password(self, db):
        assert PASSWORD not in run()
