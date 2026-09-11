from django.urls import path

from . import views

app_name = "images"

urlpatterns = [
    path("generate/", views.GenerateImageView.as_view(), name="generate"),
    path("options/", views.GenerationOptionsView.as_view(), name="options"),
    path("quota/", views.QuotaView.as_view(), name="quota"),
    path("bulk-delete/", views.BulkDeleteImagesView.as_view(), name="bulk-delete"),
    path(
        "prompts/",
        views.SavedPromptListCreateView.as_view(),
        name="saved-prompt-list",
    ),
    path(
        "prompts/<int:pk>/",
        views.SavedPromptDetailView.as_view(),
        name="saved-prompt-detail",
    ),
    path(
        "prompts/<int:pk>/use/",
        views.SavedPromptUseView.as_view(),
        name="saved-prompt-use",
    ),
    path(
        "shared/<str:token>/",
        views.SharedImageView.as_view(),
        name="shared-image",
    ),
    path(
        "shares/<int:pk>/",
        views.ShareLinkRevokeView.as_view(),
        name="share-revoke",
    ),
    path("<int:pk>/share/", views.ShareLinkView.as_view(), name="share"),
    path("<int:pk>/", views.ImageDetailView.as_view(), name="detail"),
    path("", views.ImageListView.as_view(), name="list"),
]
