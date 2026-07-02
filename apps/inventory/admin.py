from django.contrib import admin
from .models import Part, Supplier, CSVUpload


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "quantity", "supplier", "created_at")
    list_filter = ("supplier", "created_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    list_display = ("id", "uploaded_by", "status", "rows_processed", "rows_failed", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("uploaded_by__username", "error_message")
    readonly_fields = ("status", "rows_processed", "rows_failed", "error_message", "celery_task_id", "created_at", "updated_at")
    ordering = ("-created_at",)
