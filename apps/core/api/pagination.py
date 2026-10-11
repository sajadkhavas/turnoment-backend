import re

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ContractPagination(PageNumberPagination):
    """Opt-in page envelope aligned with frozen list contracts, not a global override."""

    page_size = 20
    page_size_query_param = "pageSize"
    max_page_size = 100

    def get_page_size(self, request):
        raw = request.query_params.get(self.page_size_query_param)
        if raw is None:
            return self.page_size
        if not re.fullmatch(r"[0-9]{1,3}", raw) or not 1 <= int(raw) <= self.max_page_size:
            raise ValidationError({"pageSize": ["Must be an integer from 1 to 100."]})
        return int(raw)

    def get_paginated_response(self, data):
        return Response(
            {
                "schemaVersion": 1,
                "items": data,
                "pagination": {
                    "currentPage": self.page.number,
                    "totalPages": self.page.paginator.num_pages,
                    "totalItems": self.page.paginator.count,
                    "pageSize": self.get_page_size(self.request),
                },
            }
        )
