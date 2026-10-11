from django.core.paginator import Paginator
from django.http import Http404
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.moderation.admin_site import is_platform_operator
from apps.moderation.models import ModerationCase
from apps.moderation.services import InvalidModerationTransition, review_case

from .serializers import ModerationCaseSerializer, ModerationDecisionSerializer, ReviewSerializer


class PlatformOperatorOnly(BasePermission):
    def has_permission(self, request, view):
        return is_platform_operator(request.user)


class CasesView(APIView):
    permission_classes = [PlatformOperatorOnly]

    def get(self, request):
        fields = {"source_type", "status", "center_id", "page"}
        if set(request.query_params) - fields or any(
            len(request.query_params.getlist(key)) != 1 for key in request.query_params
        ):
            return Response({"error": {"code": "invalid_filter"}}, status=400)
        source = request.query_params.get("source_type")
        status = request.query_params.get("status")
        center = request.query_params.get("center_id")
        if source and source not in ModerationCase.Source.values:
            return Response({"error": {"code": "invalid_source"}}, status=400)
        if status and status not in ModerationCase.Status.values:
            return Response({"error": {"code": "invalid_status"}}, status=400)
        try:
            page = int(request.query_params.get("page", "1"))
            if page < 1 or page > 1_000_000:
                raise ValueError
        except ValueError:
            return Response({"error": {"code": "invalid_page"}}, status=400)
        queryset = ModerationCase.objects.all()
        if source:
            queryset = queryset.filter(source_type=source)
        if status:
            queryset = queryset.filter(status=status)
        if center is not None:
            queryset = queryset.filter(center_id=center)
        pages = Paginator(queryset, 20)
        last_page = pages.num_pages if pages.count else 0
        current_page = min(page, last_page) if last_page else 1
        objects = pages.page(current_page).object_list if last_page else []
        return Response({
            "items": ModerationCaseSerializer(objects, many=True).data,
            "pagination": {
                "currentPage": current_page, "totalPages": last_page,
                "totalItems": pages.count,
            },
        })


class CaseDetailView(APIView):
    permission_classes = [PlatformOperatorOnly]

    def get_case(self, case_id):
        try:
            return ModerationCase.objects.get(pk=case_id)
        except ModerationCase.DoesNotExist as exc:
            raise Http404 from exc

    def get(self, request, case_id):
        case = self.get_case(case_id)
        return Response({
            **ModerationCaseSerializer(case).data,
            "decisions": ModerationDecisionSerializer(case.decisions.all(), many=True).data,
        })


class ReviewCaseView(APIView):
    permission_classes = [PlatformOperatorOnly]

    def post(self, request, case_id):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            case, changed = review_case(
                case_id=case_id, actor=request.user, to_status=serializer.validated_data["status"],
                note=serializer.validated_data["note"],
            )
        except ModerationCase.DoesNotExist as exc:
            raise Http404 from exc
        except InvalidModerationTransition:
            return Response({"error": {"code": "invalid_transition"}}, status=409)
        return Response({"case": ModerationCaseSerializer(case).data, "changed": changed})
