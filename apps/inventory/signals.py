import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Part

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Part)
def generate_embedding_on_part_save(sender, instance, created, **kwargs):
    """Generate embedding when a part is created or updated."""
    try:
        from .tasks import generate_part_embedding
        generate_part_embedding.delay(instance.id)
    except Exception as e:
        logger.error(f"Error queuing embedding task: {str(e)}")
