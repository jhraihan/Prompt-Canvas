from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class PasswordResetTokens(PasswordResetTokenGenerator):
    key_salt = "promptcanvas.accounts.PasswordResetTokens"

    def _make_hash_value(self, user, timestamp):
        login_timestamp = (
            ""
            if user.last_login is None
            else user.last_login.replace(microsecond=0, tzinfo=None)
        )
        return f"{user.pk}{user.password}{login_timestamp}{timestamp}{user.email}"

    def check_token(self, user, token):
        self._timeout = settings.PASSWORD_RESET_TIMEOUT
        return super().check_token(user, token)


class EmailVerificationTokens(PasswordResetTokenGenerator):
    key_salt = "promptcanvas.accounts.EmailVerificationTokens"

    def _make_hash_value(self, user, timestamp):
        verified = "" if user.email_verified_at is None else user.email_verified_at
        return f"{user.pk}{user.email}{verified}{timestamp}"

    def check_token(self, user, token):
        self._timeout = settings.EMAIL_VERIFICATION_TIMEOUT
        return super().check_token(user, token)


password_reset_tokens = PasswordResetTokens()
email_verification_tokens = EmailVerificationTokens()


def encode_uid(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def decode_uid(uidb64):
    try:
        return urlsafe_base64_decode(uidb64).decode()
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError):
        return None
