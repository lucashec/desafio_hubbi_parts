from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0004_migrate_to_pgvector"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="part",
            name="supplier",
        ),
        migrations.DeleteModel(
            name="Supplier",
        ),
    ]
