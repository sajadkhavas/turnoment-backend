from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationQuerySerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=("all", "unread", "read"), default="all")
    kind = serializers.ChoiceField(
        choices=("all", "tournament", "match", "challenge", "account", "system"),
        default="all",
    )
    page = serializers.IntegerField(min_value=1, max_value=1_000_000, default=1)


class NotificationSerializer(serializers.ModelSerializer):
    notificationId = serializers.UUIDField(source="id", format="hex_verbose", read_only=True)
    occurredAt = serializers.DateTimeField(source="occurred_at", read_only=True)
    readAt = serializers.DateTimeField(source="read_at", read_only=True)
    target = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ("notificationId", "kind", "title", "body", "occurredAt", "readAt", "target")

    def get_target(self, obj):
        if not obj.target_kind:
            return None
        key = {
            "tournament-detail": "tournamentSlug",
            "result-submission": "matchId",
            "match-dispute": "matchId",
        }.get(obj.target_kind)
        if key:
            return {"kind": obj.target_kind, key: obj.target_id}
        return {"kind": obj.target_kind}
