from rest_framework import serializers
from .models import ApiKey, IntegrationLog


class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ["id", "key", "name", "is_active", "created_at", "last_used_at"]
        read_only_fields = ["key", "is_active", "created_at", "last_used_at"]


class IntegrationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationLog
        fields = ["id", "api_key", "action", "status", "payload", "response", "error_message", "created_at"]


class InventoryUpdateSerializer(serializers.Serializer):
    part_id = serializers.IntegerField(help_text="ID da peça a atualizar")
    quantity_delta = serializers.IntegerField(help_text="Alteração na quantidade (positivo ou negativo)")
    
    def validate_part_id(self, value):
        if value <= 0:
            raise serializers.ValidationError("O ID da peça deve ser positivo.")
        return value
