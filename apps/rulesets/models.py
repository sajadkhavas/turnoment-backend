import uuid

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from apps.games.models import PUBLIC_SLUG


class Ruleset(models.Model):
    """Reviewed, versioned policy text. Never an executable money/refund command."""

    class Publication(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        "games.Game", on_delete=models.PROTECT, null=True, blank=True, related_name="rulesets",
    )
    key = models.CharField(max_length=96, validators=[RegexValidator(PUBLIC_SLUG)])
    revision = models.CharField(max_length=40)
    publication_state = models.CharField(
        max_length=12, choices=Publication.choices, default=Publication.DRAFT,
    )
    title = models.CharField(max_length=180)
    summary = models.CharField(max_length=1200)
    effective_on = models.DateField(null=True, blank=True)
    sections = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("key", "-created_at")
        constraints = [
            models.UniqueConstraint(fields=["key", "revision"], name="ruleset_key_rev_unique"),
            models.UniqueConstraint(
                fields=["key"], condition=Q(publication_state="published"),
                name="ruleset_one_published_key",
            ),
            models.CheckConstraint(
                condition=Q(publication_state__in=["draft", "published", "archived"]),
                name="ruleset_publication_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["publication_state", "key"], name="rulesets_public_key_idx"),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if not isinstance(self.sections, list) or not (1 <= len(self.sections) <= 12):
            errors["sections"] = "Provide between 1 and 12 sections."
        else:
            section_ids = set()
            rule_ids = set()
            for section in self.sections:
                if not isinstance(section, dict) or set(section) != {
                    "id", "title", "description", "rules",
                }:
                    errors["sections"] = "Invalid section shape."
                    break
                sid = section.get("id")
                if not self._key(sid) or sid in section_ids:
                    errors["sections"] = "Invalid or duplicated section ID."
                    break
                section_ids.add(sid)
                if not self._text(section.get("title"), 180) or not self._text(
                    section.get("description"), 700
                ):
                    errors["sections"] = "Invalid section content."
                    break
                rules = section.get("rules")
                if not isinstance(rules, list) or not (1 <= len(rules) <= 12):
                    errors["sections"] = "Each section needs 1 to 12 rules."
                    break
                for rule in rules:
                    if not isinstance(rule, dict) or set(rule) != {"id", "title", "body"}:
                        errors["sections"] = "Invalid rule shape."
                        break
                    rid = rule.get("id")
                    if (
                        not self._key(rid) or rid in rule_ids
                        or not self._text(rule.get("title"), 180)
                        or not self._text(rule.get("body"), 2400)
                    ):
                        errors["sections"] = "Invalid or duplicated rule."
                        break
                    rule_ids.add(rid)
                if errors:
                    break
        if not self.revision.strip():
            errors["revision"] = "A revision is required."
        if not self.title.strip() or not self.summary.strip():
            errors["title"] = "Reviewed policy text is required."
        if errors:
            raise ValidationError(errors)

    @staticmethod
    def _key(value):
        import re

        return isinstance(value, str) and bool(re.fullmatch(PUBLIC_SLUG, value)) and len(value) <= 96

    @staticmethod
    def _text(value, limit):
        return isinstance(value, str) and 1 <= len(value.strip()) <= limit and value == value.strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
