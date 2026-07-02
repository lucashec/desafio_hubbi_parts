# Generated migration to migrate from BinaryField to pgvector VectorField

from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_part_embedding_part_embedding_model_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
        migrations.RemoveField(
            model_name="part",
            name="embedding",
        ),
        migrations.AddField(
            model_name="part",
            name="embedding",
            field=pgvector.django.VectorField(
                blank=True,
                dimensions=384,
                help_text="Vector embedding for semantic search (RAG) - 384-dimensional (all-MiniLM-L6-v2)",
                null=True,
            ),
        ),
    ]
