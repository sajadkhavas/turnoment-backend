import time

from django.core.management.base import BaseCommand

from apps.notifications.delivery import dispatch_one
from apps.rankings.services import drain_b08_events


class Command(BaseCommand):
    help = "Process durable ranking events and queued player deliveries."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=int, default=5)

    def handle(self, *args, **options):
        while True:
            try:
                count = drain_b08_events(limit=100)
                if count:
                    self.stdout.write(f"Applied ranking events: {count}")
            except Exception as exc:
                self.stderr.write(f"Ranking drain failed ({type(exc).__name__}); events retained")
            for _ in range(100):
                if not dispatch_one():
                    break
            if options["once"]:
                return
            time.sleep(max(1, options["interval"]))
