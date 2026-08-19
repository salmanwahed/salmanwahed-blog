from django.conf import settings
from django.core.cache import caches
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Flush a cache from the command line.

    The site already exposes /clear-cache/, but that needs a logged-in session
    and a running web process. This works from a shell, a deploy script or a
    container, which is where you usually want it after publishing a post: the
    list and detail views are cached for 15 minutes and the projects page for
    45, so new content is otherwise invisible until the entry expires.
    """

    help = "Clear a Django cache. Defaults to the 'default' alias."

    def add_arguments(self, parser):
        parser.add_argument(
            "--alias",
            default="default",
            help="Cache alias from settings.CACHES to clear (default: 'default').",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Clear every configured cache alias instead of just one.",
        )

    def handle(self, *args, **options):
        if options["all"]:
            aliases = list(settings.CACHES)
        else:
            alias = options["alias"]
            if alias not in settings.CACHES:
                configured = ", ".join(sorted(settings.CACHES))
                raise CommandError(f"No cache alias {alias!r} in settings.CACHES. Configured: {configured}.")
            aliases = [alias]

        for alias in aliases:
            cache = caches[alias]
            try:
                cache.clear()
            except Exception as exc:
                # A dead Redis is the common case. Report it as a command
                # failure with a non-zero exit code rather than a traceback, so
                # a deploy script can act on it.
                raise CommandError(f"Could not clear cache {alias!r}: {exc}") from exc

            backend = type(cache).__name__
            self.stdout.write(self.style.SUCCESS(f"Cleared cache {alias!r} ({backend})."))
