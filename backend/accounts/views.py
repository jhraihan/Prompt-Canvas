import logging

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import send_email_verification, send_password_reset
from .security import (
    TrustedOrigin,
    clear_refresh_cookie,
    read_refresh_cookie,
    set_refresh_cookie,
)
from .serializers import (
    AuthPayloadSerializer,
    ChangePasswordSerializer,
    EmailVerificationConfirmSerializer,
    LoginRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)

logger = logging.getLogger("promptcanvas.auth")
User = get_user_model()


def _auth_payload(user, refresh):
    return {
        "access": str(refresh.access_token),
        "user": UserSerializer(user).data,
    }


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        send_email_verification(user)

        refresh = RefreshToken.for_user(user)
        response = Response(_auth_payload(user, refresh), status=status.HTTP_201_CREATED)
        return set_refresh_cookie(response, refresh)


@extend_schema(
    tags=["auth"],
    summary="Sign in",
    request=LoginRequestSerializer,
    responses={
        200: AuthPayloadSerializer,
        401: OpenApiResponse(description="Bad credentials"),
    },
    description=(
        "Returns an access token in the body and sets the refresh token as an "
        "httpOnly cookie. The refresh token is never in the response body."
    ),
)
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = TokenObtainPairSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        refresh = RefreshToken(serializer.validated_data["refresh"])
        response = Response(_auth_payload(user, refresh), status=status.HTTP_200_OK)
        return set_refresh_cookie(response, refresh)


@extend_schema(
    tags=["auth"],
    summary="Exchange the refresh cookie for a new access token",
    request=None,
    responses={
        200: AuthPayloadSerializer,
        401: OpenApiResponse(description="Session ended"),
    },
    description="Reads the httpOnly refresh cookie; rotates it on every use.",
)
class RefreshView(APIView):
    permission_classes = [AllowAny, TrustedOrigin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token"

    def post(self, request):
        raw = read_refresh_cookie(request)
        if not raw:
            return Response(
                {"detail": "Your session has ended. Please sign in again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(raw)
            user = User.objects.get(pk=refresh["user_id"], is_active=True)
            refresh.blacklist()
            new_refresh = RefreshToken.for_user(user)
        except (TokenError, User.DoesNotExist, KeyError) as exc:
            logger.info("Refresh rejected: %s", exc.__class__.__name__)
            response = Response(
                {"detail": "Your session has ended. Please sign in again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            return clear_refresh_cookie(response)

        response = Response(_auth_payload(user, new_refresh), status=status.HTTP_200_OK)
        return set_refresh_cookie(response, new_refresh)


@extend_schema(
    tags=["auth"],
    summary="Sign out",
    request=None,
    responses={
        204: OpenApiResponse(description="Cookie cleared and token blacklisted"),
    },
)
class LogoutView(APIView):
    permission_classes = [AllowAny, TrustedOrigin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token"

    def post(self, request):
        raw = read_refresh_cookie(request)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        return clear_refresh_cookie(response)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["auth"],
    summary="Change password",
    request=ChangePasswordSerializer,
    responses={200: AuthPayloadSerializer},
)
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        response = Response(_auth_payload(user, refresh), status=status.HTTP_200_OK)
        return set_refresh_cookie(response, refresh)


@extend_schema(
    tags=["auth"],
    summary="Request a password reset link",
    request=PasswordResetRequestSerializer,
    responses={
        202: OpenApiResponse(
            description="Always returned, whether or not the address exists"
        ),
    },
    description=(
        "Answers identically for a known and an unknown address so the "
        "endpoint cannot be used to discover which addresses have accounts."
    ),
)
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    NEUTRAL_RESPONSE = {
        "detail": (
            "If an account exists for that address, a reset link is on its way. "
            "Check your inbox, and your spam folder."
        )
    }

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email, is_active=True).first()
        if user is not None:
            send_password_reset(user)
            logger.info("Password reset requested for user id=%s", user.pk)
        else:
            logger.info("Password reset requested for an unknown address")

        return Response(self.NEUTRAL_RESPONSE, status=status.HTTP_202_ACCEPTED)


@extend_schema(
    tags=["auth"],
    summary="Redeem a password reset link",
    request=PasswordResetConfirmSerializer,
    responses={
        200: AuthPayloadSerializer,
        400: OpenApiResponse(description="Invalid or expired link"),
    },
    description=(
        "Single use: completing a reset invalidates every outstanding link and "
        "every existing session for the account."
    ),
)
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        _revoke_all_refresh_tokens(user)
        logger.info("Password reset completed for user id=%s", user.pk)

        refresh = RefreshToken.for_user(user)
        response = Response(_auth_payload(user, refresh), status=status.HTTP_200_OK)
        return set_refresh_cookie(response, refresh)


@extend_schema(
    tags=["auth"],
    summary="Resend the email confirmation",
    request=None,
    responses={
        202: OpenApiResponse(description="Sent"),
        200: OpenApiResponse(description="Already confirmed"),
    },
)
class EmailVerificationRequestView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        if request.user.is_email_verified:
            return Response(
                {"detail": "Your email address is already confirmed."},
                status=status.HTTP_200_OK,
            )
        send_email_verification(request.user)
        return Response(
            {"detail": "Confirmation email sent. Check your inbox."},
            status=status.HTTP_202_ACCEPTED,
        )


@extend_schema(
    tags=["auth"],
    summary="Confirm an email address",
    request=EmailVerificationConfirmSerializer,
    responses={
        200: OpenApiResponse(description="Confirmed"),
        400: OpenApiResponse(description="Invalid or expired link"),
    },
)
class EmailVerificationConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("Email verified for user id=%s", user.pk)
        return Response(
            {
                "detail": "Your email address is confirmed.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


def _revoke_all_refresh_tokens(user):
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
