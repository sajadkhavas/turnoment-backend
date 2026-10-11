from django.core.paginator import Paginator
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.services import mark_all_read, mark_one_read

from .serializers import NotificationQuerySerializer, NotificationSerializer


class InboxView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if set(request.query_params) - {"state", "kind", "page"}:
            return Response({"error": {"code": "invalid_filter"}}, status=400)
        params = NotificationQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        query = params.validated_data
        mine = Notification.objects.filter(recipient=request.user)
        summary = {
            "total": mine.count(),
            "unread": mine.filter(read_at__isnull=True).count(),
        }
        filtered = mine
        if query["state"] == "read":
            filtered = filtered.filter(read_at__isnull=False)
        elif query["state"] == "unread":
            filtered = filtered.filter(read_at__isnull=True)
        if query["kind"] != "all":
            filtered = filtered.filter(kind=query["kind"])
        pages = Paginator(filtered, 5)
        total_pages = pages.num_pages if pages.count else 0
        current = min(query["page"], total_pages) if total_pages else 1
        entries = pages.page(current).object_list if total_pages else []
        return Response({
            "summary": summary,
            "items": NotificationSerializer(entries, many=True).data,
            "pagination": {
                "currentPage": current,
                "totalPages": total_pages,
                "totalItems": pages.count,
            },
        })


class ReadNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        if request.data:
            return Response({"error": {"code": "unexpected_payload"}}, status=400)
        try:
            notification, unread = mark_one_read(
                recipient_id=request.user.pk, notification_id=notification_id
            )
        except Notification.DoesNotExist as exc:
            raise Http404 from exc
        return Response({
            "outcome": "saved",
            "notificationId": str(notification.id),
            "readAt": NotificationSerializer(notification).data["readAt"],
            "unreadCount": unread,
        })


class ReadAllNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.data:
            return Response({"error": {"code": "unexpected_payload"}}, status=400)
        marked, timestamp, unread = mark_all_read(recipient_id=request.user.pk)
        from rest_framework.fields import DateTimeField
        return Response({
            "outcome": "saved",
            "markedCount": marked,
            "readAt": DateTimeField().to_representation(timestamp),
            "unreadCount": unread,
        })
