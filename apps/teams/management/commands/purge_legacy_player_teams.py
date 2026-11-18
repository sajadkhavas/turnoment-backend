from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.registrations.models import Registration
from apps.teams.models import Team


class Command(BaseCommand):
    help = "Preview legacy team removal; apply only when no registrations reference them."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        legacy = Team.objects.filter(center__isnull=True)
        ids = [str(pk) for pk in legacy.select_for_update().values_list("pk", flat=True)]
        references = Registration.objects.filter(team_id__in=ids).count()
        self.stdout.write(f"legacy_teams={len(ids)} related_registrations={references}")
        if options["apply"]:
            if references:
                raise CommandError("Resolve linked registrations before removing teams.")
            deleted, _ = legacy.delete()
            self.stdout.write(f"deleted_rows={deleted}")
