from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


def is_platform_operator(user):
    # Being center staff, or merely having is_staff=True, must never confer
    # platform-wide privileges. P01 superusers are the conservative initial authority.
    return bool(
        user.is_authenticated and user.is_active and user.is_staff and user.is_superuser
    )


class PlatformAdminSite(AdminSite):
    site_header = "Turnoment platform operations"

    def has_permission(self, request):
        return is_platform_operator(request.user)


class PlatformAdminConfig(AdminConfig):
    default_site = "apps.moderation.admin_site.PlatformAdminSite"
