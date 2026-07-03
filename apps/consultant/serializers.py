from rest_framework import serializers
from .models import ConsultantQuery, ConsultantResponse


class ConsultantQueryInputSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=1000, help_text="Pergunta para o consultor de IA")
    
    def validate_query(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("A pergunta não pode estar vazia.")
        return value.strip()


class ConsultantQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultantQuery
        fields = ["id", "user", "query_text", "created_at"]


class ConsultantResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultantResponse
        fields = ["id", "query", "response_text", "created_at"]
