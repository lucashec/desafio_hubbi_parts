from django.db import models
import uuid


class ApiKey(models.Model):
    key = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def is_valid(self) -> bool:
        return self.is_active

    def get_masked_key(self) -> str:
        if len(self.key) > 8:
            return f"{self.key[:4]}...{self.key[-4:]}"
        return "****"


class IntegrationLog(models.Model):
    STATUS_CHOICES = [
        ("success", "Sucesso"),
        ("error", "Erro"),
        ("pending", "Pendente"),
        ("retry", "Tentando novamente"),
    ]

    api_key = models.ForeignKey(
        ApiKey,
        on_delete=models.CASCADE,
        related_name="logs"
    )
    action = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payload = models.JSONField(null=True, blank=True)
    response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    processing_time = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Integração"
        verbose_name_plural = "Logs de Integração"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["api_key"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} - {self.status}"

    def is_successful(self) -> bool:
        return self.status == "success"

    def get_processing_time_formatted(self) -> str:
        return f"{self.processing_time:.2f}s"
