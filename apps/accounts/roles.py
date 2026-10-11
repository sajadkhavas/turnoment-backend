"""B02 role helpers; central operator policy and memberships are owner domains."""

from rest_framework.permissions import BasePermission

from apps.moderation.admin_site import is_platform_operator as is_platform_operator


def has_center_role(user, *, membership, center_id, manager_only=False):
    """Honor B04 durable owner/manager/staff roles without global staff escalation."""
    if not user.is_authenticated or not user.is_active or membership is None:
        return False
    if membership.user_id != user.pk or str(membership.center_id) != str(center_id):
        return False
    if not getattr(membership, "is_active", False):
        return False
    permitted = {"owner", "manager"} if manager_only else {"owner", "manager", "staff"}
    return membership.role in permitted


class IsPlatformOperator(BasePermission):
    def has_permission(self, request, view):
        return is_platform_operator(request.user)
