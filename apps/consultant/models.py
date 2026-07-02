from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class ConsultantQuery(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("processing", "Processando"),
        ("completed", "Concluído"),
        ("error", "Erro"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="consultant_queries"
    )
    query_text = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Query do Consultor"
        verbose_name_plural = "Queries do Consultor"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.query_text[:50]}"

    def is_completed(self) -> bool:
        return self.status == "completed"


class ConsultantResponse(models.Model):
    query = models.OneToOneField(
        ConsultantQuery,
        on_delete=models.CASCADE,
        related_name="response"
    )
    response_text = models.TextField()
    tokens_used = models.IntegerField(default=0)
    processing_time = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Resposta do Consultor"
        verbose_name_plural = "Respostas do Consultor"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Resposta para {self.query.user.email}"

    def get_processing_time_formatted(self) -> str:
        return f"{self.processing_time:.2f}s"
