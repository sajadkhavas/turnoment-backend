import secrets
from dataclasses import dataclass
from typing import ClassVar

from django.conf import settings
from django.utils.module_loading import import_string


class OtpDeliveryUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OtpDelivery:
    phone: str
    code: str


class DisabledOtpSender:
    def send(self, delivery: OtpDelivery) -> None:
        raise OtpDeliveryUnavailable("OTP delivery is not configured.")


class ConsoleOtpSender:
    def send(self, delivery: OtpDelivery) -> None:
        if not settings.DEBUG:
            raise OtpDeliveryUnavailable("Console OTP delivery is disabled outside DEBUG mode.")
        print(f"[turnoment-local-otp] phone={delivery.phone} code={delivery.code}")  # noqa: T201


class MemoryOtpSender:
    outbox: ClassVar[list[OtpDelivery]] = []

    def send(self, delivery: OtpDelivery) -> None:
        self.outbox.append(delivery)

    @classmethod
    def clear(cls) -> None:
        cls.outbox.clear()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def get_otp_sender():
    sender_class = import_string(settings.OTP_SENDER_BACKEND)
    return sender_class()
