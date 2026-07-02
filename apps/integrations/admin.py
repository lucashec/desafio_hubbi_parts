from django.contrib import admin
from .models import ApiKey, IntegrationLog


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "key", "is_active", "created_at", "last_used_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "key")
    ordering = ("-created_at",)


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ("id", "api_key", "action", "status", "created_at")
    list_filter = ("status", "action", "created_at")
    search_fields = ("api_key__name", "action")
    ordering = ("-created_at",)
