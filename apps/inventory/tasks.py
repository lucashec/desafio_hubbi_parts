import csv
import logging
from decimal import Decimal
from celery import shared_task
from django.core.files.storage import default_storage
from .models import CSVUpload, Part

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_csv_upload(self, csv_upload_id):
    """
    Processa um arquivo CSV enviado pelo usuário.
    Importa peças e gera embeddings automaticamente.
    Formato esperado: nome,descricao,preco,quantidade_inicial
    """
    try:
        csv_upload = CSVUpload.objects.get(id=csv_upload_id)
        csv_upload.status = "processing"
        csv_upload.celery_task_id = self.request.id
        csv_upload.save()
        
        file_path = csv_upload.file.path
        rows_processed = 0
        rows_failed = 0
        parts_created = []
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            if not reader.fieldnames:
                raise ValueError("CSV file is empty")
            
            required_fields = {'nome', 'descricao', 'preco', 'quantidade_inicial'}
            if not required_fields.issubset(set(reader.fieldnames)):
                missing = required_fields - set(reader.fieldnames)
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    name = row.get('nome', '').strip()
                    description = row.get('descricao', '').strip()
                    price_str = row.get('preco', '').strip()
                    quantity_str = row.get('quantidade_inicial', '').strip()
                    
                    if not name or not price_str or not quantity_str:
                        rows_failed += 1
                        logger.warning(f"Row {row_num}: Missing required fields")
                        continue
                    
                    try:
                        price = Decimal(price_str)
                        quantity = int(quantity_str)
                    except (ValueError, TypeError):
                        rows_failed += 1
                        logger.warning(f"Row {row_num}: Invalid price or quantity format")
                        continue
                    
                    if price <= 0 or quantity < 0:
                        rows_failed += 1
                        logger.warning(f"Row {row_num}: Invalid price or quantity values")
                        continue
                    
                    part, created = Part.objects.get_or_create(
                        name=name,
                        defaults={
                            'description': description,
                            'price': price,
                            'quantity': quantity,
                        }
                    )
                    
                    if not created:
                        part.price = price
                        part.quantity = quantity
                        part.description = description
                        part.save()
                    
                    parts_created.append(part.id)
                    rows_processed += 1
                
                except Exception as e:
                    rows_failed += 1
                    logger.error(f"Row {row_num}: {str(e)}")
                    continue
        
        csv_upload.status = "completed"
        csv_upload.rows_processed = rows_processed
        csv_upload.rows_failed = rows_failed
        csv_upload.save()
        
        logger.info(
            f"CSV Upload {csv_upload_id}: "
            f"Processed {rows_processed} rows, {rows_failed} failed"
        )
        
        if parts_created:
            generate_embeddings_for_parts.delay(parts_created)
            logger.info(f"Queued embedding generation for {len(parts_created)} parts")
        
    except CSVUpload.DoesNotExist:
        logger.error(f"CSVUpload with id {csv_upload_id} not found")
    except Exception as e:
        logger.error(f"Error processing CSV {csv_upload_id}: {str(e)}")
        csv_upload.status = "error"
        csv_upload.error_message = str(e)
        csv_upload.save()


@shared_task
def generate_embeddings_for_parts(part_ids):
    """
    Generates embeddings for multiple parts in a single task.
    More efficient than queuing individual tasks.
    """
    if not part_ids:
        return {"success": 0, "failed": 0}
    
    try:
        from services.vector_search_service import VectorSearchService
        
        model = get_embedding_model()
        search_service = VectorSearchService(model=model)
        
        parts = Part.objects.filter(id__in=part_ids)
        success = 0
        failed = 0
        
        for part in parts:
            try:
                if search_service._generate_and_save_embedding(part):
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed to generate embedding for part {part.id}: {str(e)}")
                failed += 1
        
        logger.info(f"Generated embeddings for {success} parts, {failed} failed")
        return {"success": success, "failed": failed}
    except Exception as e:
        logger.error(f"Error in batch embedding generation: {str(e)}")
        return {"success": 0, "failed": len(part_ids), "error": str(e)}


_embedding_model = None


def get_embedding_model():
    """
    Cache global para o modelo de embedding.
    Carrega o modelo uma única vez e reutiliza em todas as tarefas.
    """
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model (sentence-transformers)...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
    return _embedding_model


@shared_task
def generate_part_embedding(part_id):
    """
    Generates embedding for a part with optimized model caching.
    Called asynchronously when a part is created or updated.
    """
    try:
        part = Part.objects.get(id=part_id)
        from services.vector_search_service import VectorSearchService
        
        model = get_embedding_model()
        search_service = VectorSearchService(model=model)
        
        if search_service._generate_and_save_embedding(part):
            logger.info(f"Generated embedding for part {part_id}")
        else:
            logger.warning(f"Failed to generate embedding for part {part_id}")
    except Part.DoesNotExist:
        logger.error(f"Part {part_id} not found")
    except Exception as e:
        logger.error(f"Error generating embedding for part {part_id}: {str(e)}")


@shared_task
def regenerate_all_embeddings():
    """
    Regenerates embeddings for all parts.
    Can be called periodically or on demand.
    """
    try:
        from services.vector_search_service import VectorSearchService
        
        model = get_embedding_model()
        search_service = VectorSearchService(model=model)
        success, failed = search_service.regenerate_all_embeddings()
        logger.info(f"Regenerated all embeddings: {success} success, {failed} failed")
        return {"success": success, "failed": failed}
    except Exception as e:
        logger.error(f"Error regenerating all embeddings: {str(e)}")
        return {"success": 0, "failed": -1, "error": str(e)}

