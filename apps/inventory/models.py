from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from core.validators import validate_positive_number


User = get_user_model()


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    catalog_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Part(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    quantity = models.IntegerField(default=0, validators=[validate_positive_number])
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parts"
    )
    embedding = models.BinaryField(
        null=True,
        blank=True,
        help_text="Vector embedding for semantic search (RAG)"
    )
    embedding_model = models.CharField(
        max_length=100,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help_text="Embedding model used to generate this vector"
    )
    embedding_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When embedding was last updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Peça"
        verbose_name_plural = "Peças"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["supplier"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    def is_available(self) -> bool:
        return self.quantity > 0

    def get_display_price(self) -> str:
        return f"R$ {self.price:.2f}"


class CSVUpload(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("processing", "Processando"),
        ("completed", "Concluído"),
        ("error", "Erro"),
    ]
    
    file = models.FileField(upload_to="csv_uploads/%Y/%m/%d/")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="csv_uploads"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    rows_processed = models.IntegerField(default=0)
    rows_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Upload CSV"
        verbose_name_plural = "Uploads CSV"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["uploaded_by"]),
            models.Index(fields=["-created_at"]),
        ]
    
    def __str__(self) -> str:
        return f"CSV Upload - {self.uploaded_by} ({self.status})"
