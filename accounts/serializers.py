from rest_framework import serializers
from django.utils import timezone
from .models import User, PrivacyConsent


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "role",
            "employee_id",
            "company",
            "shift",
            "utilization",
            "is_active",
            "employee_status",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "employee_id",
            "company",
            "is_active",
            "active_as_of",
            "employee_status",
            "shift",
            "utilization",
            "latitude",
            "longitude",
            "street_name",
            "address_number",
            "neighborhood",
            "postal_code",
            "district",
            "state",
            "country",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "utilization",
            "shift",
            "latitude",
            "longitude",
            "street_name",
            "address_number",
            "neighborhood",
            "postal_code",
            "district",
            "state",
            "country",
            "company",
            "is_active",
            "employee_status",
            "active_as_of",
        ]


class PrivacyConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyConsent
        fields = ["accepted", "accepted_at", "version", "location_granted"]
        read_only_fields = ["accepted_at"]

    def update(self, instance, validated_data):
        accepted_before = instance.accepted
        instance.accepted = validated_data.get("accepted", instance.accepted)
        instance.location_granted = validated_data.get("location_granted", instance.location_granted)
        instance.version = validated_data.get("version", instance.version)

        if instance.accepted and (not accepted_before or instance.accepted_at is None):
            instance.accepted_at = timezone.now()
        elif not instance.accepted:
            instance.accepted_at = None

        instance.save()
        return instance