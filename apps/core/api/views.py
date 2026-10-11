from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView

from apps.core.api.errors import core_exception_handler
from apps.core.api.pagination import ContractPagination


class CoreErrorMixin:
    """Integration seam: exceptions only, never modify authentication/permissions."""

    def get_exception_handler(self):
        return core_exception_handler


class CoreAPIView(CoreErrorMixin, APIView):
    pass


class CoreGenericAPIView(CoreErrorMixin, GenericAPIView):
    pagination_class = ContractPagination
