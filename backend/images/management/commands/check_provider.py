import time

from django.core.management.base import BaseCommand, CommandError

from images.constants import QUALITY_STANDARD, SIZE_SQUARE, parse_size, quality_profile
from images.exceptions import GenerationError
from images.services.providers import GenerationRequest, get_provider
from images.services.storage import get_storage


class Command(BaseCommand):
    help = "Generate one image with the configured provider and report the result."

    def add_arguments(self, parser):
        parser.add_argument("--prompt", default="A calm harbour at sunrise, wide shot")
        parser.add_argument("--size", default=SIZE_SQUARE)
        parser.add_argument("--quality", default=QUALITY_STANDARD)
        parser.add_argument(
            "--save",
            action="store_true",
            help="Also write the image through the configured storage backend.",
        )

    def handle(self, *args, **options):
        try:
            provider = get_provider()
        except GenerationError as exc:
            raise CommandError(f"Provider could not start: {exc.user_message}") from exc

        description = provider.describe()
        self.stdout.write(f"Provider: {description['provider']}")
        self.stdout.write(f"Model:    {description['model']}")

        width, height = parse_size(options["size"])
        profile = quality_profile(description["model"], options["quality"])
        self.stdout.write(f"Size:     {width} x {height}")
        self.stdout.write(f"Sampler:  {profile}")
        self.stdout.write("Generating...")

        started = time.monotonic()
        try:
            asset = provider.generate(
                GenerationRequest(
                    prompt=options["prompt"],
                    width=width,
                    height=height,
                    quality=options["quality"],
                )
            )
        except GenerationError as exc:
            raise CommandError(
                f"{exc.__class__.__name__}: {exc.user_message}\n"
                f"Check the server log for the provider diagnostic."
            ) from exc

        elapsed = time.monotonic() - started
        self.stdout.write(
            self.style.SUCCESS(
                f"OK - {len(asset.image_bytes):,} bytes, "
                f"{asset.width} x {asset.height}, in {elapsed:.1f}s"
            )
        )

        if options["save"]:
            stored = get_storage().save(
                f"generated/smoke-test.{asset.extension}",
                asset.image_bytes,
                asset.content_type,
            )
            self.stdout.write(self.style.SUCCESS(f"Saved to {stored.url}"))
