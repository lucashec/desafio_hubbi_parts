import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Part

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Part)
def generate_embedding_on_part_save(
    sender,
    instance,
    created,
    update_fields=None,
    **kwargs,
):
    if update_fields is not None:
        embedding_fields = {
            "embedding",
            "embedding_model",
            "embedding_updated_at",
            "updated_at",
        }

        if set(update_fields).issubset(embedding_fields):
            return

    try:
        from .tasks import generate_part_embedding

        generate_part_embedding.delay(instance.id)

    except Exception as e:
        logger.error(f"Error queuing embedding task: {str(e)}")