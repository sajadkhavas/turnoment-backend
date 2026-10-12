"""B99 operator drain for committed B08 finalizations into replay-safe B09 ratings."""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.rankings.services import drain_b08_events


class Command(BaseCommand):
    help = "Apply finalized B08 result events chronologically, once per event."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=100,
            help="Maximum unconsumed finalized events to apply (1–1000).",
        )

    def handle(self, *args, **options):
        try:
            applied = drain_b08_events(limit=options["limit"])
        except ValidationError as exc:
            raise CommandError(
                "Ranking drain blocked: configure an unambiguous season and "
                "repair event ordering before retrying."
            ) from exc
        self.stdout.write(self.style.SUCCESS(f"Applied {applied} B08 events."))
