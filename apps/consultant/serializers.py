from rest_framework import serializers
from .models import ConsultantQuery, ConsultantResponse


class ConsultantQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultantQuery
        fields = ["id", "user", "query_text", "created_at"]


class ConsultantResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultantResponse
        fields = ["id", "query", "response_text", "created_at"]
