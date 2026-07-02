from rest_framework import serializers
from .models import Part, Supplier, CSVUpload


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = ["id", "name", "description", "price", "quantity", "supplier", "created_at", "updated_at"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "catalog_url", "created_at"]

class CSVUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVUpload
        fields = ["id", "file", "status", "rows_processed", "rows_failed", "error_message", "created_at", "updated_at"]
        read_only_fields = ["status", "rows_processed", "rows_failed", "error_message", "created_at", "updated_at"]


class CSVUploadStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVUpload
        fields = ["id", "status", "rows_processed", "rows_failed", "error_message", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "rows_processed", "rows_failed", "error_message", "created_at", "updated_at"]
