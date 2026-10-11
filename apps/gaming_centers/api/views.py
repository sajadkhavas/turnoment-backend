import math
import re
import uuid

from django.db import connection, transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gaming_resources.models import Equipment, OpeningHour, Station

from ..models import CenterMembership, City, GamingCenter
from ..services import RateLimitExceeded, receive_host_application
from .serializers import CenterProfileSerializer, HostApplicationInputSerializer

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _published():
    return GamingCenter.objects.filter(publication_state=GamingCenter.Publication.PUBLISHED)


def _city(city):
    return {"cityId": str(city.id), "slug": city.slug, "name": city.name}


def _labels(center, limit=16):
    return list(
        center.equipment.filter(is_public=True).order_by("label")
        .values_list("label", flat=True)[:limit]
    )


def _center_item(center):
    return {
        "centerId": str(center.id),
        "publicId": center.public_id,
        "publicationState": "published",
        "name": center.name,
        "verified": center.verified,
        "city": _city(center.city),
        "district": center.district,
        "summary": center.summary,
        "equipmentLabels": _labels(center, 12),
        "coverImage": center.cover_image or None,
        "upcomingTournamentCount": center.upcoming_tournament_count,
    }


class CenterDirectoryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params
        if set(params) - {"city", "page"} or any(
            len(params.getlist(key)) != 1 for key in params
        ):
            return Response({"query": ["Unknown or duplicate filter."]}, status=400)
        city = params.get("city")
        page_value = params.get("page", "1")
        if not re.fullmatch(r"[0-9]{1,9}", page_value) or int(page_value) < 1:
            return Response({"page": ["Must be a positive integer."]}, status=400)
        if city is not None and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", city):
            return Response({"city": ["Invalid slug."]}, status=400)
        page = int(page_value)
        qs = _published().select_related("city").order_by("name", "id")
        facets = (
            City.objects.filter(centers__publication_state=GamingCenter.Publication.PUBLISHED)
            .annotate(count=Count("centers")).order_by("name", "id")[:100]
        )
        if city is not None:
            qs = qs.filter(city__slug=city)
        total = qs.count()
        per_page = 20
        pages = max(1, math.ceil(total / per_page))
        if page > pages:
            raise Http404
        items = [_center_item(center) for center in qs[(page - 1) * per_page:page * per_page]]
        return Response({
            "schemaVersion": 1,
            "filters": {"cities": [{**_city(item), "count": item.count} for item in facets]},
            "activeQuery": {**({"city": city} if city is not None else {}), "page": page},
            "items": items,
            "pagination": {
                "currentPage": page, "totalPages": pages,
                "totalItems": total, "pageSize": per_page,
            },
        })


class CenterDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, public_id):
        center = get_object_or_404(
            _published().select_related("city"), public_id=public_id
        )
        address = None
        if center.show_address:
            address = {
                "streetAddress": center.street_address,
                "addressLocality": center.address_locality,
                "addressRegion": center.address_region or None,
                "postalCode": center.postal_code or None,
                "addressCountry": "IR",
                "displayAddress": center.display_address,
            }
        hours = [
            {"dayOfWeek": [DAY_NAMES[h.weekday]],
             "opens": h.opens.strftime("%H:%M"), "closes": h.closes.strftime("%H:%M")}
            for h in center.hours.filter(is_public=True).order_by("weekday")
        ]
        return Response({
            "schemaVersion": 1,
            **_center_item(center),
            "description": center.description,
            "equipmentLabels": _labels(center),
            "galleryImages": list(
                center.gallery.filter(is_public=True).order_by("position")
                .values_list("image_url", flat=True)[:8]
            ),
            "publicAddress": address,
            "publicPhone": center.business_phone if center.show_phone else None,
            "openingHours": hours,
            "mapUrl": center.map_url if center.show_map else None,
            # Seam for B05; never manufacture a tournament or authoritative zero.
            "tournaments": [],
        })


class HostApplicationView(APIView):
    authentication_classes = []  # F23: session independent, no incidental CSRF difference.
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            if int(request.META.get("CONTENT_LENGTH") or 0) > 8192:
                return Response({"detail": "Request too large."}, status=400)
        except ValueError:
            return Response({"detail": "Invalid content length."}, status=400)
        if not isinstance(request.data, dict) or type(request.data.get("stationCount")) is not int:
            return Response({"detail": "Invalid JSON fields."}, status=400)
        payload = HostApplicationInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            application = receive_host_application(
                payload.validated_data, request.META.get("REMOTE_ADDR", "")
            )
        except RateLimitExceeded as exc:
            response = Response({"detail": "Rate limit exceeded."}, status=429)
            response["Retry-After"] = str(exc.retry_after)
            return response
        return Response({
            "schemaVersion": 1,
            "applicationId": application.id.hex,
            "state": "received",
            "submittedAt": application.submitted_at.isoformat(),
        }, status=201)


def _scope(request, center_id, allowed):
    center = get_object_or_404(GamingCenter, id=center_id)
    scope_query = CenterMembership.objects.filter(
        center=center, user=request.user, is_active=True
    )
    if connection.in_atomic_block:
        scope_query = scope_query.select_for_update()
    membership = scope_query.first()
    if not membership or membership.role not in allowed:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Center membership required.")
    return center, membership


EDIT_ROLES = [CenterMembership.Role.OWNER, CenterMembership.Role.MANAGER]


class CenterProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES + [CenterMembership.Role.STAFF])
        return Response({
            "centerId": str(center.id),
            "publicId": center.public_id,
            "publicationState": center.publication_state,
            "verified": center.verified,
            **CenterProfileSerializer(center).data,
        })

    @transaction.atomic
    def patch(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        serializer = CenterProfileSerializer(center, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CenterStaffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        records = center.memberships.order_by("joined_at")
        return Response({
            "items": [{"membershipId": str(m.id), "userId": str(m.user_id),
                       "role": m.role, "active": m.is_active} for m in records]
        })

    @transaction.atomic
    def post(self, request, center_id):
        center, _ = _scope(request, center_id, [CenterMembership.Role.OWNER])
        GamingCenter.objects.select_for_update().get(pk=center.pk)
        user_id = request.data.get("userId")
        role = request.data.get("role")
        if role not in [CenterMembership.Role.MANAGER, CenterMembership.Role.STAFF]:
            return Response({"role": ["Only manager/staff can be assigned."]}, status=400)
        try:
            user_id = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return Response({"userId": ["Invalid identifier."]}, status=400)
        from django.contrib.auth import get_user_model
        user = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
        if CenterMembership.objects.filter(center=center, user=user).exists():
            return Response({"detail": "Membership already exists."}, status=409)
        membership = CenterMembership.objects.create(center=center, user=user, role=role)
        return Response({"membershipId": str(membership.id), "role": membership.role}, status=201)


class CenterStaffDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, center_id, membership_id):
        center, _ = _scope(request, center_id, [CenterMembership.Role.OWNER])
        member = get_object_or_404(
            CenterMembership.objects.select_for_update(), pk=membership_id, center=center
        )
        if member.role == CenterMembership.Role.OWNER:
            return Response({"detail": "Owners are managed by platform review."}, status=403)
        if set(request.data) != {"role", "active"}:
            return Response({"detail": "role and active required."}, status=400)
        if request.data["role"] not in [CenterMembership.Role.MANAGER, CenterMembership.Role.STAFF]:
            return Response({"role": ["Invalid role."]}, status=400)
        if type(request.data["active"]) is not bool:
            return Response({"active": ["Boolean required."]}, status=400)
        member.role = request.data["role"]
        member.is_active = request.data["active"]
        member.save(update_fields=["role", "is_active"])
        return Response({"membershipId": str(member.id), "role": member.role,
                         "active": member.is_active})


class CenterEquipmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES + [CenterMembership.Role.STAFF])
        return Response({"items": [
            {"equipmentId": str(e.id), "label": e.label, "isPublic": e.is_public}
            for e in center.equipment.order_by("label")
        ]})

    @transaction.atomic
    def post(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        if set(request.data) != {"label", "isPublic"}:
            return Response({"detail": "label and isPublic required."}, status=400)
        label = request.data.get("label")
        public = request.data.get("isPublic")
        if (not isinstance(label, str) or not 1 <= len(label.strip()) <= 240
                or type(public) is not bool):
            return Response({"detail": "Invalid equipment."}, status=400)
        GamingCenter.objects.select_for_update().get(pk=center.pk)
        if center.equipment.filter(label__iexact=label.strip()).exists():
            return Response({"detail": "Duplicate equipment."}, status=409)
        equipment = Equipment.objects.create(center=center, label=label.strip(), is_public=public)
        return Response({"equipmentId": str(equipment.id)}, status=201)


class CenterStationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES + [CenterMembership.Role.STAFF])
        return Response({"items": [
            {"stationId": str(s.id), "code": s.code, "equipmentId": str(s.equipment_id),
             "state": s.state}
            for s in center.stations.order_by("code")
        ]})

    @transaction.atomic
    def post(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        GamingCenter.objects.select_for_update().get(pk=center.pk)
        if set(request.data) != {"code", "equipmentId"}:
            return Response({"detail": "code and equipmentId required."}, status=400)
        code = request.data.get("code")
        if not isinstance(code, str) or not 1 <= len(code.strip()) <= 40:
            return Response({"code": ["Invalid code."]}, status=400)
        try:
            equipment_id = uuid.UUID(str(request.data["equipmentId"]))
        except (ValueError, TypeError, AttributeError):
            return Response({"equipmentId": ["Invalid identifier."]}, status=400)
        equipment = get_object_or_404(Equipment, pk=equipment_id, center=center)
        if center.stations.filter(code=code.strip()).exists():
            return Response({"detail": "Duplicate station."}, status=409)
        station = Station.objects.create(center=center, equipment=equipment, code=code.strip())
        return Response({"stationId": str(station.id)}, status=201)


class CenterOpeningHoursView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES + [CenterMembership.Role.STAFF])
        return Response({"items": [
            {"weekday": h.weekday, "opens": h.opens.strftime("%H:%M"),
             "closes": h.closes.strftime("%H:%M"), "isPublic": h.is_public}
            for h in center.hours.order_by("weekday")
        ]})

    @transaction.atomic
    def put(self, request, center_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        GamingCenter.objects.select_for_update().get(pk=center.pk)
        class HoursSerializer(serializers.Serializer):
            weekday = serializers.IntegerField(min_value=0, max_value=6)
            opens = serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])
            closes = serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])
            isPublic = serializers.BooleanField()

            def validate(self, attrs):
                if attrs["opens"] >= attrs["closes"]:
                    raise serializers.ValidationError("opens must precede closes.")
                return attrs

        if not isinstance(request.data, list) or len(request.data) > 7:
            return Response({"detail": "Maximum seven weekday rules."}, status=400)
        parsed = HoursSerializer(data=request.data, many=True)
        parsed.is_valid(raise_exception=True)
        days = [h["weekday"] for h in parsed.validated_data]
        if len(days) != len(set(days)):
            return Response({"detail": "Duplicate weekday."}, status=400)
        center.hours.all().delete()
        OpeningHour.objects.bulk_create([
            OpeningHour(center=center, weekday=h["weekday"], opens=h["opens"],
                        closes=h["closes"], is_public=h["isPublic"])
            for h in parsed.validated_data
        ])
        return self.get(request, center_id)


class CenterEquipmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, center_id, equipment_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        GamingCenter.objects.select_for_update().get(pk=center.pk)
        equipment = get_object_or_404(
            Equipment.objects.select_for_update(), pk=equipment_id, center=center
        )
        if not request.data or set(request.data) - {"label", "isPublic"}:
            return Response({"detail": "Invalid equipment update."}, status=400)
        if "label" in request.data:
            label = request.data["label"]
            if not isinstance(label, str) or not 1 <= len(label.strip()) <= 240:
                return Response({"label": ["Invalid equipment label."]}, status=400)
            label = label.strip()
            if center.equipment.exclude(pk=equipment.pk).filter(label__iexact=label).exists():
                return Response({"detail": "Duplicate equipment."}, status=409)
            equipment.label = label
        if "isPublic" in request.data:
            if type(request.data["isPublic"]) is not bool:
                return Response({"isPublic": ["Boolean required."]}, status=400)
            equipment.is_public = request.data["isPublic"]
        equipment.save()
        return Response({
            "equipmentId": str(equipment.id), "label": equipment.label,
            "isPublic": equipment.is_public
        })

    @transaction.atomic
    def delete(self, request, center_id, equipment_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        GamingCenter.objects.select_for_update().get(pk=center.pk)
        equipment = get_object_or_404(
            Equipment.objects.select_for_update(), pk=equipment_id, center=center
        )
        if equipment.stations.exists():
            return Response({"detail": "Equipment is assigned to stations."}, status=409)
        equipment.delete()
        return Response(status=204)


class CenterStationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, center_id, station_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        station = get_object_or_404(
            Station.objects.select_for_update(), pk=station_id, center=center
        )
        if set(request.data) != {"state"} or request.data["state"] not in Station.State.values:
            return Response({"state": ["Invalid station state."]}, status=400)
        station.state = request.data["state"]
        station.save(update_fields=["state"])
        return Response({"stationId": str(station.id), "state": station.state})

    @transaction.atomic
    def delete(self, request, center_id, station_id):
        center, _ = _scope(request, center_id, EDIT_ROLES)
        station = get_object_or_404(
            Station.objects.select_for_update(), pk=station_id, center=center
        )
        station.delete()
        return Response(status=204)
