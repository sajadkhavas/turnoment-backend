import pytest
from django.core.exceptions import ValidationError

from apps.accounts.phone import normalize_iran_mobile


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("09121234567", "+989121234567"),
        ("+989121234567", "+989121234567"),
        ("989121234567", "+989121234567"),
        ("00989121234567", "+989121234567"),
        ("9121234567", "+989121234567"),
        ("۰۹۱۲۱۲۳۴۵۶۷", "+989121234567"),
        ("٠٩١٢١٢٣٤٥٦٧", "+989121234567"),
        ("0912 123 4567", "+989121234567"),
    ],
)
def test_normalize_iran_mobile(raw, expected):
    assert normalize_iran_mobile(raw) == expected


@pytest.mark.parametrize("raw", ["", "02112345678", "0912123456", "+9891212345678", "not-a-phone"])
def test_normalize_iran_mobile_rejects_invalid_values(raw):
    with pytest.raises(ValidationError):
        normalize_iran_mobile(raw)
