import re

from rest_framework import serializers

from apps.accounts.phone import normalize_iran_mobile

from ..models import GamingCenter


class HostApplicationInputSerializer(serializers.Serializer):
    venueName = serializers.CharField(min_length=2, max_length=120, trim_whitespace=True)
    managerName = serializers.CharField(min_length=2, max_length=120, trim_whitespace=True)
    phone = serializers.CharField(max_length=32, trim_whitespace=True)
    city = serializers.CharField(min_length=2, max_length=80, trim_whitespace=True)
    area = serializers.CharField(min_length=2, max_length=120, trim_whitespace=True)
    stationCount = serializers.IntegerField(min_value=1, max_value=1000)
    games = serializers.CharField(min_length=2, max_length=300, trim_whitespace=True)
    description = serializers.CharField(
        min_length=1, max_length=1200, trim_whitespace=True, allow_null=True, required=False
    )

    def validate_phone(self, value):
        try:
            number = normalize_iran_mobile(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Invalid Iranian mobile.") from None
        if not re.fullmatch(r"\+989\d{9}", number):
            raise serializers.ValidationError("Invalid Iranian mobile.")
        return number

    def validate(self, attrs):
        if set(self.initial_data) != set(self.fields) - {"description"} and (
            set(self.initial_data) != set(self.fields)
        ):
            raise serializers.ValidationError("Unknown or missing application fields.")
        attrs.setdefault("description", None)
        return attrs


class CenterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GamingCenter
        fields = [
            "name", "district", "summary", "description", "cover_image",
            "street_address", "address_locality", "address_region", "postal_code",
            "display_address", "show_address", "business_phone", "show_phone",
            "map_url", "show_map",
        ]

    def validate(self, attrs):
        instance = self.instance
        data = {name: attrs.get(name, getattr(instance, name)) for name in self.fields}
        if len(data["summary"].strip()) < 20 or len(data["description"].strip()) < 40:
            raise serializers.ValidationError("Summary/description is too short.")
        if data["show_phone"] and not re.fullmatch(
            r"\+?[0-9۰-۹٠-٩ ()-]{7,32}", data["business_phone"]
        ):
            raise serializers.ValidationError({"business_phone": "Valid public phone required."})
        if data["show_address"] and (
            len(data["street_address"].strip()) < 3
            or len(data["display_address"].strip()) < 5
            or not data["address_locality"].strip()
        ):
            raise serializers.ValidationError({"show_address": "Complete public address required."})
        if data["show_map"] and not data["map_url"]:
            raise serializers.ValidationError({"map_url": "A map URL is required."})
        return attrs
