import uuid

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator
from django.db import models
from django.db.models import Q


GAME_KEY = r"^[A-Za-z0-9_-]{1,128}$"
PUBLIC_SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def new_game_id():
    return "g_" + uuid.uuid4().hex


class Game(models.Model):
    class Publication(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.CharField(
        max_length=128, primary_key=True, default=new_game_id,
        validators=[RegexValidator(GAME_KEY)],
    )
    slug = models.CharField(
        max_length=128, unique=True, validators=[RegexValidator(PUBLIC_SLUG)],
    )
    publication_state = models.CharField(
        max_length=12, choices=Publication.choices, default=Publication.DRAFT,
    )
    name = models.CharField(max_length=240)
    short_name = models.CharField(max_length=240)
    description = models.TextField(validators=[MinLengthValidator(20), MaxLengthValidator(700)])
    platforms = models.JSONField(default=list)
    cover_image = models.CharField(max_length=2048, null=True, blank=True)
    hero_image = models.CharField(max_length=2048, null=True, blank=True)
    detail_version = models.CharField(max_length=80, default="1")
    seo_title = models.CharField(max_length=180, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")
        indexes = [
            models.Index(
                fields=["publication_state", "sort_order", "id"],
                name="games_public_order_idx",
            ),
            GinIndex(
                SearchVector("name", "short_name", "description", config="simple"),
                name="games_public_search_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(publication_state__in=["draft", "published", "archived"]),
                name="games_publication_valid",
            ),
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.platforms, list) or not (1 <= len(self.platforms) <= 8):
            raise ValidationError({"platforms": "Choose between 1 and 8 platforms."})
        if any(
            not isinstance(value, str)
            or not value.strip()
            or len(value.strip()) > 240
            or value != value.strip()
            for value in self.platforms
        ):
            raise ValidationError({"platforms": "Platforms must be nonblank labels."})
        if len(set(self.platforms)) != len(self.platforms):
            raise ValidationError({"platforms": "Platforms must be unique."})
        if self.cover_image is not None and not self.cover_image.strip():
            raise ValidationError({"cover_image": "Use null or a nonblank URL."})
        if self.hero_image is not None and not self.hero_image.strip():
            raise ValidationError({"hero_image": "Use null or a nonblank URL."})
        if self.pk:
            previous = Game.objects.filter(pk=self.pk).values_list("slug", flat=True).first()
            if previous is not None and previous != self.slug:
                raise ValidationError({"slug": "Canonical slugs cannot be changed."})
        if self.name != self.name.strip() or self.short_name != self.short_name.strip():
            raise ValidationError("Names must be trimmed.")
        if not self.name.strip() or not self.short_name.strip():
            raise ValidationError("Names cannot be blank.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CompetitiveFormat(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="competitive_formats")
    key = models.CharField(max_length=96, validators=[RegexValidator(PUBLIC_SLUG)])
    label = models.CharField(max_length=240)
    description = models.TextField(validators=[MinLengthValidator(1)])
    team_size = models.PositiveSmallIntegerField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(fields=["game", "key"], name="games_format_key_unique"),
            models.CheckConstraint(
                condition=Q(team_size__isnull=True) | Q(team_size__gt=0),
                name="games_format_team_size_positive",
            ),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
