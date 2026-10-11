from rest_framework import serializers

from apps.moderation.models import ModerationCase, ModerationDecision


class ReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("in_review", "closed"))
    note = serializers.CharField(min_length=10, max_length=1000, trim_whitespace=True)


class ModerationCaseSerializer(serializers.ModelSerializer):
    caseId = serializers.UUIDField(source="id", format="hex_verbose", read_only=True)
    sourceType = serializers.CharField(source="source_type", read_only=True)
    sourceId = serializers.CharField(source="source_id", read_only=True)
    centerId = serializers.CharField(source="center_id", read_only=True)
    openedAt = serializers.DateTimeField(source="opened_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = ModerationCase
        fields = (
            "caseId", "sourceType", "sourceId", "centerId", "title", "status",
            "openedAt", "updatedAt",
        )


class ModerationDecisionSerializer(serializers.ModelSerializer):
    fromStatus = serializers.CharField(source="from_status", read_only=True)
    toStatus = serializers.CharField(source="to_status", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ModerationDecision
        fields = ("fromStatus", "toStatus", "note", "createdAt")
