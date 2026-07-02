from django.contrib import admin
from .models import ConsultantQuery, ConsultantResponse


@admin.register(ConsultantQuery)
class ConsultantQueryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "query_text", "created_at")
    list_filter = ("user", "created_at")
    search_fields = ("user__email", "query_text")
    ordering = ("-created_at",)


@admin.register(ConsultantResponse)
class ConsultantResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "query", "created_at")
    list_filter = ("created_at",)
    search_fields = ("query__user__email", "response_text")
    ordering = ("-created_at",)
