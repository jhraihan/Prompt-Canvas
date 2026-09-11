from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Create or reset the shared demo account."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--display-name", default="Demo")
        parser.add_argument(
            "--clear-history",
            action="store_true",
            help="Also delete every image the demo account has generated.",
        )

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"]

        if len(password) < 8:
            raise CommandError("The demo password must be at least 8 characters.")

        user, created = User.objects.get_or_create(
            email=email, defaults={"display_name": options["display_name"]}
        )

        user.set_password(password)
        user.display_name = options["display_name"]
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.save()

        action = "Created" if created else "Reset"
        self.stdout.write(self.style.SUCCESS(f"{action} demo account {email}"))

        if options["clear_history"]:
            from images.services.generation import delete_image

            count = 0
            for image in user.images.all():
                delete_image(image)
                count += 1
            self.stdout.write(self.style.SUCCESS(f"Cleared {count} demo image(s)"))

        self.stdout.write(
            "Set VITE_DEMO_EMAIL and VITE_DEMO_PASSWORD in Vercel to match, "
            "then redeploy the frontend."
        )
