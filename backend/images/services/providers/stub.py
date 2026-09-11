import io

from PIL import Image, ImageDraw

from images.constants import quality_profile

from .base import GeneratedAsset, GenerationRequest, ImageProvider


class StubProvider(ImageProvider):
    name = "stub"

    def __init__(self, model="stub/gradient", **_):
        self.model = model

    def describe(self):
        return {"provider": self.name, "model": self.model}

    def generate(self, request: GenerationRequest) -> GeneratedAsset:
        model = request.model or self.model
        quality_profile(model, request.quality)

        image = Image.new("RGB", (request.width, request.height))
        draw = ImageDraw.Draw(image)
        seed = sum(request.prompt.encode()) % 256
        for y in range(request.height):
            ratio = y / max(request.height - 1, 1)
            draw.line(
                [(0, y), (request.width, y)],
                fill=(seed, int(40 + 120 * ratio), int(200 - 120 * ratio)),
            )

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return GeneratedAsset(
            image_bytes=buffer.getvalue(),
            content_type="image/png",
            provider=self.name,
            model=model,
            width=request.width,
            height=request.height,
        )
