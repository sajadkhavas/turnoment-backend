from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rulesets.selectors import policy_detail, policy_summary, published_rulesets


class PublicRulesetAPIView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]


class RulesetListView(PublicRulesetAPIView):
    def get(self, request):
        if request.query_params:
            raise ValidationError({"query": "Unexpected query parameter."})
        policies = list(published_rulesets()[:101])
        if len(policies) > 100:
            return Response({"error": {"code": "rulesets_capacity_exceeded"}}, status=503)
        return Response({
            "schemaVersion": 1, "totalItems": len(policies),
            "items": [policy_summary(policy) for policy in policies],
        })


class RulesetDetailView(PublicRulesetAPIView):
    def get(self, request, key):
        policy = get_object_or_404(published_rulesets(), key=key)
        return Response(policy_detail(policy))
