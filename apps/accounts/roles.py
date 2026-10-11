"""Role checks are deliberately separate from Django's is_staff/superuser flags.

Center membership is B04-owned; a caller must pass the B04 membership scope.
Never infer venue access from a globally named group.
"""
from rest_framework.permissions import BasePermission

PLATFORM_OPERATOR = "platform_operator"
CENTER_STAFF = "center_staff"
CENTER_MANAGER = "center_manager"


def is_platform_operator(user):
    return bool(
        user.is_authenticated and user.is_active
        and (user.is_superuser or user.groups.filter(name=PLATFORM_OPERATOR).exists())
    )


def has_center_role(user, *, membership, center_id, manager_only=False):
    if not user.is_authenticated or not user.is_active or membership is None:
        return False
    if membership.user_id != user.pk or membership.center_id != center_id:
        return False
    if not getattr(membership, "is_active", False):
        return False
    permitted = {CENTER_MANAGER} if manager_only else {CENTER_STAFF, CENTER_MANAGER}
    return membership.role in permitted


class IsPlatformOperator(BasePermission):
    def has_permission(self, request, view):
        return is_platform_operator(request.user)
