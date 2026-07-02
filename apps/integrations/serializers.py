from rest_framework import serializers
from .models import ApiKey, IntegrationLog


class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ["id", "key", "name", "is_active", "created_at", "last_used_at"]


class IntegrationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationLog
        fields = ["id", "api_key", "action", "status", "payload", "response", "error_message", "created_at"]
