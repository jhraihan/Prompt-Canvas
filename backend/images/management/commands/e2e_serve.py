import pathlib

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Reset a throwaway SQLite database, migrate, and serve. For E2E only."

    def add_arguments(self, parser):
        parser.add_argument("port", nargs="?", default="8100")

    def handle(self, *args, **options):
        database = settings.DATABASES["default"]

        if "sqlite" not in database["ENGINE"]:
            raise CommandError(
                "e2e_serve only runs against SQLite. Refusing to touch "
                f"{database['ENGINE']}."
            )

        path = pathlib.Path(str(database["NAME"]))
        if path.is_absolute() and not str(path).startswith(str(settings.BASE_DIR)):
            raise CommandError(
                f"Refusing to delete a database outside the project: {path}"
            )

        if path.exists():
            path.unlink()
            self.stdout.write(f"Dropped {path.name}")

        call_command("migrate", "--noinput", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Migrated. Starting server..."))

        call_command("runserver", options["port"], "--noreload", use_reloader=False)
