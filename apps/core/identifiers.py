"""Frontend-aligned ASCII public identifiers; auth UUIDs remain under P01."""

import re
from uuid import UUID

from rest_framework.exceptions import ValidationError

PUBLIC_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,128}", re.ASCII)


def public_id(value: object) -> str:
    """Validate without coercion, normalization, or confusable substitutions."""
    if not isinstance(value, str) or not PUBLIC_ID_PATTERN.fullmatch(value):
        raise ValidationError({"id": ["Invalid public identifier."]}, code="invalid_identifier")
    return value


def uuid_public_id(value: UUID) -> str:
    """Serialize UUID database keys to frontend-compatible stable IDs."""
    if not isinstance(value, UUID):
        raise TypeError("Expected a UUID")
    return str(value)
