import logging

from django.conf import settings
from django.core.mail import send_mail

from .tokens import email_verification_tokens, encode_uid, password_reset_tokens

logger = logging.getLogger("promptcanvas.auth")


def _link(path, user, token):
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    return f"{base}{path}?uid={encode_uid(user)}&token={token}"


def _send(subject, body, user):
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Failed to send %r to user id=%s", subject, user.pk)
        return False


def send_password_reset(user):
    token = password_reset_tokens.make_token(user)
    link = _link("/reset-password", user, token)
    hours = max(1, settings.PASSWORD_RESET_TIMEOUT // 3600)

    body = f"""Hello {user.get_short_name()},

Someone asked to reset the password for your Prompt Canvas account.

Choose a new password:

{link}

This link work once and expires in {hours} hour{"s" if hours != 1 else ""}.

If this wasn't you, you can ignore this email — your password has not changed
and nobody can use this link without access to your inbox.

— Prompt Canvas
"""
    return _send("Reset your Prompt Canvas password", body, user)


def send_email_verification(user):
    token = email_verification_tokens.make_token(user)
    link = _link("/verify-email", user, token)
    days = max(1, settings.EMAIL_VERIFICATION_TIMEOUT // 86400)

    body = f"""Hello {user.get_short_name()},

Welcome to Prompt Canvas. Confirm this address so we can reach you if you ever
need to reset your password:

{link}

This link expires in {days} day{"s" if days != 1 else ""}.

You can keep using your account in the meantime — verifying is not required to
generate images.

If you didn't create this account, you can ignore this email.

— Prompt Canvas
"""
    return _send("Confirm your Prompt Canvas email", body, user)
