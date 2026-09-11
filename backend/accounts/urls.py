from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", views.RefreshView.as_view(), name="refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("password/", views.ChangePasswordView.as_view(), name="change-password"),
    path(
        "password/reset/",
        views.PasswordResetRequestView.as_view(),
        name="password-reset",
    ),
    path(
        "password/reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "email/verify/",
        views.EmailVerificationConfirmView.as_view(),
        name="email-verify",
    ),
    path(
        "email/verify/request/",
        views.EmailVerificationRequestView.as_view(),
        name="email-verify-request",
    ),
]
