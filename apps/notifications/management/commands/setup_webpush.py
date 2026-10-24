import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Generate local VAPID keys without printing or committing the private key."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--subject", required=True)

    def handle(self, *args, **options):
        destination = Path(options["output"]).resolve()
        if destination.exists():
            raise CommandError("Key configuration already exists; do not replace active keys.")
        if not options["subject"].startswith(("mailto:", "https://")):
            raise CommandError("Subject must be a mailto or https contact.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        key = ec.generate_private_key(ec.SECP256R1())
        private_path = destination.with_suffix(".pem")
        if private_path.exists():
            raise CommandError("Private key file already exists.")
        pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        descriptor = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(pem)
        public = key.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )
        data = {
            "PUSH_VAPID_PRIVATE_KEY": str(private_path),
            "PUSH_VAPID_PUBLIC_KEY": base64.urlsafe_b64encode(public).rstrip(b"=").decode(),
            "PUSH_VAPID_SUBJECT": options["subject"],
        }
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        self.stdout.write("Local push configuration created. Keep both files private.")
