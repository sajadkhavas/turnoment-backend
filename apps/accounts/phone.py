import re

from django.core.exceptions import ValidationError

_IRAN_E164_RE = re.compile(r"^\+989\d{9}$")
_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_iran_mobile(value: str) -> str:
    if value is None:
        raise ValidationError("شماره موبایل الزامی است.")

    normalized = str(value).strip().translate(_PERSIAN_DIGITS)
    normalized = re.sub(r"[\s\-()]", "", normalized)

    if normalized.startswith("0098"):
        normalized = f"+98{normalized[4:]}"
    elif normalized.startswith("98"):
        normalized = f"+{normalized}"
    elif normalized.startswith("0"):
        normalized = f"+98{normalized[1:]}"
    elif normalized.startswith("9"):
        normalized = f"+98{normalized}"

    if not _IRAN_E164_RE.fullmatch(normalized):
        raise ValidationError("شماره موبایل ایران معتبر نیست.")

    return normalized


def validate_iran_mobile(value: str) -> None:
    normalized = normalize_iran_mobile(value)
    if normalized != value:
        raise ValidationError("شماره موبایل باید به فرمت E.164 ذخیره شود.")
