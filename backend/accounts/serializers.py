from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email_verified = serializers.BooleanField(source="is_email_verified", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "display_name",
            "date_joined",
            "email_verified",
        )
        read_only_fields = ("id", "email", "date_joined", "email_verified")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("id", "email", "display_name", "password")

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value, self.context["request"].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "invalid_link": (
            "This reset link is invalid or has expired. Please request a new one."
        ),
    }

    def validate(self, attrs):
        from .tokens import decode_uid, password_reset_tokens

        user_id = decode_uid(attrs["uid"])
        if user_id is None:
            self.fail("invalid_link")

        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except (User.DoesNotExist, ValueError, TypeError):
            self.fail("invalid_link")

        if not password_reset_tokens.check_token(user, attrs["token"]):
            self.fail("invalid_link")

        try:
            validate_password(attrs["new_password"], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"new_password": list(exc.messages)}
            ) from exc

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class EmailVerificationConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    default_error_messages = {
        "invalid_link": (
            "This confirmation link is invalid or has expired. Please request a new one."
        ),
    }

    def validate(self, attrs):
        from .tokens import decode_uid, email_verification_tokens

        user_id = decode_uid(attrs["uid"])
        if user_id is None:
            self.fail("invalid_link")

        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except (User.DoesNotExist, ValueError, TypeError):
            self.fail("invalid_link")

        if not email_verification_tokens.check_token(user, attrs["token"]):
            self.fail("invalid_link")

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.mark_email_verified()
        return user


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AuthPayloadSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True, help_text="Short-lived access token.")
    user = UserSerializer(read_only=True)
