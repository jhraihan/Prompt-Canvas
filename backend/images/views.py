import logging
from datetime import timedelta

from django.http import Http404
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .constants import MODEL_CATALOGUE, QUALITY_CHOICES, SIZE_CHOICES
from .models import GeneratedImage, SavedPrompt, ShareLink
from .quota import generation_quota
from .serializers import (
    BulkDeleteSerializer,
    GeneratedImageSerializer,
    GenerationRequestSerializer,
    SavedPromptSerializer,
    SharedImageSerializer,
    ShareLinkCreateSerializer,
    ShareLinkSerializer,
)
from .services.generation import delete_image, generate_image, provider_metadata

logger = logging.getLogger("promptcanvas.api")


class OwnedByUserMixin:
    permission_classes = [IsAuthenticated]


class OwnedImagesMixin(OwnedByUserMixin):
    serializer_class = GeneratedImageSerializer

    def get_queryset(self):
        return GeneratedImage.objects.filter(user=self.request.user)


@extend_schema(
    tags=["images"],
    summary="Generate an image",
    request=GenerationRequestSerializer,
    responses={
        201: GeneratedImageSerializer,
        400: OpenApiResponse(description="Validation failed"),
        429: OpenApiResponse(description="Generation rate limit reached"),
    },
    description=(
        "The response carries the saved generation plus a `quota` object "
        "describing what is left in the current window."
    ),
)
class GenerateImageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "generation"

    def post(self, request):
        serializer = GenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = generate_image(user=request.user, **serializer.validated_data)
        return Response(
            {
                **GeneratedImageSerializer(image).data,
                "quota": generation_quota(request),
            },
            status=status.HTTP_201_CREATED,
        )


class ImageListView(OwnedImagesMixin, generics.ListAPIView):
    """GET /api/images/ -- the signed-in user's history, newest first."""


class ImageDetailView(OwnedImagesMixin, generics.RetrieveDestroyAPIView):
    def perform_destroy(self, instance):
        logger.info("Deleting image id=%s user=%s", instance.pk, self.request.user.pk)
        delete_image(instance)


@extend_schema(
    tags=["images"],
    summary="Generations left in the current window",
    responses={200: OpenApiResponse(description="Current quota")},
)
class QuotaView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get(self, request):
        return Response({"quota": generation_quota(request)})


@extend_schema(
    tags=["system"],
    summary="Supported sizes, qualities, and models",
    responses={200: OpenApiResponse(description="Options the generator accepts")},
)
class GenerationOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "sizes": [
                    {"value": value, "label": label, "aspect": _aspect(value)}
                    for value, label in SIZE_CHOICES
                ],
                "qualities": [
                    {"value": value, "label": label} for value, label in QUALITY_CHOICES
                ],
                "models": [dict(entry) for entry in MODEL_CATALOGUE],
                **provider_metadata(),
            }
        )


@extend_schema(
    tags=["system"],
    summary="Liveness probe",
    responses={200: OpenApiResponse(description="Status plus the active provider")},
    description=(
        "`degraded` is true when the stub provider is live, which would mean "
        "placeholder images are being served."
    ),
)
class HealthView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        metadata = provider_metadata()
        provider = metadata.get("provider")
        degraded = provider in (None, "stub")
        return Response(
            {
                "status": "ok",
                "provider": provider,
                "model": metadata.get("model"),
                "degraded": degraded,
            }
        )


def _aspect(size):
    width, _, height = size.partition("x")
    return f"{width} / {height}"


class SavedPromptListCreateView(OwnedByUserMixin, generics.ListCreateAPIView):
    serializer_class = SavedPromptSerializer
    pagination_class = None

    def get_queryset(self):
        return SavedPrompt.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SavedPromptDetailView(OwnedByUserMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavedPromptSerializer
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return SavedPrompt.objects.filter(user=self.request.user)


@extend_schema(
    tags=["images"],
    summary="Record reuse of a saved prompt",
    request=None,
    responses={200: SavedPromptSerializer, 404: OpenApiResponse(description="Not found")},
)
class SavedPromptUseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        prompt = SavedPrompt.objects.filter(user=request.user, pk=pk).first()
        if prompt is None:
            raise Http404
        prompt.record_use()
        return Response(SavedPromptSerializer(prompt).data)


@extend_schema(
    tags=["images"],
    summary="Delete several generations",
    request=BulkDeleteSerializer,
    responses={200: OpenApiResponse(description="How many were deleted")},
    description="Ids belonging to another account are skipped, not reported.",
)
class BulkDeleteImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]

        images = list(GeneratedImage.objects.filter(user=request.user, pk__in=ids))
        for image in images:
            delete_image(image)

        logger.info("Bulk deleted %s image(s) for user=%s", len(images), request.user.pk)
        return Response({"deleted": len(images), "requested": len(ids)})


@extend_schema_view(
    get=extend_schema(
        tags=["sharing"],
        summary="List share links for an image",
        responses={200: ShareLinkSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["sharing"],
        summary="Create a share link",
        request=ShareLinkCreateSerializer,
        responses={201: ShareLinkSerializer},
    ),
)
class ShareLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def _image(self, request, pk):
        image = GeneratedImage.objects.filter(user=request.user, pk=pk).first()
        if image is None:
            raise Http404
        return image

    def get(self, request, pk):
        image = self._image(request, pk)
        links = image.share_links.all()
        return Response(ShareLinkSerializer(links, many=True).data)

    def post(self, request, pk):
        image = self._image(request, pk)
        serializer = ShareLinkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        link = ShareLink.objects.create(
            image=image,
            token=ShareLink.new_token(),
            expires_at=timezone.now()
            + timedelta(hours=serializer.validated_data["expires_in_hours"]),
        )
        logger.info("Share link created for image=%s user=%s", image.pk, request.user.pk)
        return Response(ShareLinkSerializer(link).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["sharing"],
    summary="Revoke a share link",
    responses={204: OpenApiResponse(description="Revoked")},
)
class ShareLinkRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        link = ShareLink.objects.filter(pk=pk, image__user=request.user).first()
        if link is None:
            raise Http404
        link.revoke()
        logger.info("Share link revoked id=%s user=%s", link.pk, request.user.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["sharing"],
    summary="View a shared image",
    auth=[],
    parameters=[
        OpenApiParameter(
            "token", str, OpenApiParameter.PATH, description="The share token."
        )
    ],
    responses={
        200: SharedImageSerializer,
        404: OpenApiResponse(
            description="Unknown, expired, or revoked -- indistinguishable by design"
        ),
    },
)
class SharedImageView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def get(self, request, token):
        link = ShareLink.objects.filter(token=token).select_related("image").first()
        if link is None or not link.is_active:
            raise Http404

        link.record_view()
        return Response(SharedImageSerializer(link.image).data)
