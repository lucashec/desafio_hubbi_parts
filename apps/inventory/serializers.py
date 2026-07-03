from rest_framework import serializers
from .models import Part, CSVUpload
import csv
import io


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = ["id", "name", "description", "price", "quantity", "embedding_model", "embedding_updated_at", "created_at", "updated_at"]
        read_only_fields = [ "embedding_model", "embedding_updated_at", "created_at", "updated_at"]


class CSVUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVUpload
        fields = ["id", "file", "status", "rows_processed", "rows_failed", "error_message", "created_at", "updated_at"]
        read_only_fields = ["status", "rows_processed", "rows_failed", "error_message", "created_at", "updated_at"]
    
    def validate_file(self, file):
        if not file:
            raise serializers.ValidationError("File is required.")
        
        if file.size == 0:
            raise serializers.ValidationError("Uploaded file cannot be empty.")
        
        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        
        allowed_extensions = ['csv', 'txt']
        file_extension = file.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}. "
                f"Received: {file_extension}"
            )
        
        try:
            file.seek(0)
            text_content = file.read().decode('utf-8')
            file.seek(0)
            
            reader = csv.DictReader(io.StringIO(text_content))
            
            if not reader.fieldnames:
                raise serializers.ValidationError("CSV file is empty or has no headers.")
            
            required_fields = {'nome', 'descricao', 'preco', 'quantidade_inicial'}
            csv_fields = set(reader.fieldnames)
            
            if not required_fields.issubset(csv_fields):
                missing = required_fields - csv_fields
                raise serializers.ValidationError(
                    f"Missing required CSV columns: {', '.join(sorted(missing))}. "
                    f"Required columns: {', '.join(sorted(required_fields))}"
                )
            
            row_count = sum(1 for _ in reader)
            if row_count == 0:
                raise serializers.ValidationError("CSV file has no data rows (only headers).")
            
        except serializers.ValidationError:
            raise
        except UnicodeDecodeError:
            raise serializers.ValidationError(
                "File encoding error. Please ensure the file is encoded in UTF-8."
            )
        except csv.Error as e:
            raise serializers.ValidationError(f"Invalid CSV format: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"Error validating CSV file: {str(e)}")
        
        return file


class CSVUploadStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVUpload
        fields = ["id", "status", "rows_processed", "rows_failed", "error_message", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "rows_processed", "rows_failed", "error_message", "created_at", "updated_at"]
