import pytest
import io
import csv
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from apps.inventory.models import Part, Supplier, CSVUpload


User = get_user_model()


@pytest.mark.django_db
class TestCSVUpload:    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
    
    def create_csv_file(self, data):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        csv_content = output.getvalue().encode('utf-8')
        return SimpleUploadedFile(
            "test.csv",
            csv_content,
            content_type="text/csv"
        )
    
    def test_list_csv_uploads_authenticated(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/csv-uploads/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_csv_uploads_unauthenticated(self):
        response = self.client.get("/api/csv-uploads/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_csv_uploads_non_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/csv-uploads/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_csv_upload_admin(self):
        csv_data = [
            {
                'name': 'Motor V8',
                'description': 'Motor V8 3.0L',
                'price': '5000.00',
                'quantity': '10',
                'supplier_name': 'Fornecedor A'
            }
        ]
        csv_file = self.create_csv_file(csv_data)
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/csv-uploads/",
            {'file': csv_file},
            format='multipart'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
    
    def test_create_csv_upload_non_admin(self):
        csv_data = [
            {
                'name': 'Motor V8',
                'price': '5000.00',
                'quantity': '10',
                'supplier_name': 'Fornecedor A'
            }
        ]
        csv_file = self.create_csv_file(csv_data)
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/csv-uploads/",
            {'file': csv_file},
            format='multipart'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_csv_upload_status(self):
        csv_upload = CSVUpload.objects.create(
            file='test.csv',
            uploaded_by=self.admin,
            status='processing',
            rows_processed=5,
            rows_failed=2
        )
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/csv-uploads/{csv_upload.id}/status/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'processing'
        assert response.data['rows_processed'] == 5
        assert response.data['rows_failed'] == 2
    
    def test_filter_csv_uploads_by_status(self):
        CSVUpload.objects.create(
            file='test1.csv',
            uploaded_by=self.admin,
            status='pending'
        )
        CSVUpload.objects.create(
            file='test2.csv',
            uploaded_by=self.admin,
            status='completed'
        )
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/csv-uploads/?status=completed")
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]['status'] == 'completed'
