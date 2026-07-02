import pytest
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.integrations.models import ApiKey, IntegrationLog
from apps.inventory.models import Part, Supplier


User = get_user_model()


@pytest.mark.django_db
class TestApiKeyManagement:    
    def setup_method(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_create_api_key_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "ERP Integration",
            "description": "API Key para integração com ERP"
        }
        response = self.client.post("/api/api-keys/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "ERP Integration"
        assert response.data["is_active"] is True
    
    def test_create_api_key_non_admin(self):
        self.client.force_authenticate(user=self.user)
        data = {"name": "Test Key"}
        response = self.client.post("/api/api-keys/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_api_keys_admin(self):
        ApiKey.objects.create(name="Key 1")
        ApiKey.objects.create(name="Key 2")
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/api-keys/")
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        assert len(results) == 2
    
    def test_deactivate_api_key(self):
        api_key = ApiKey.objects.create(name="Test Key", is_active=True)
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f"/api/api-keys/{api_key.id}/deactivate/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False
        
        api_key.refresh_from_db()
        assert api_key.is_active is False
    
    def test_activate_api_key(self):
        api_key = ApiKey.objects.create(name="Test Key", is_active=False)
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f"/api/api-keys/{api_key.id}/activate/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is True
        
        api_key.refresh_from_db()
        assert api_key.is_active is True


@pytest.mark.django_db
class TestExternalPartSearch:    
    def setup_method(self):
        self.client = APIClient()
        self.supplier = Supplier.objects.create(name="Fornecedor A")
        Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10,
            supplier=self.supplier
        )
        Part.objects.create(
            name="Turbo Kompressor",
            price=Decimal("3000.00"),
            quantity=5,
            supplier=self.supplier
        )
        self.api_key = ApiKey.objects.create(
            name="Test Key",
            key="test-key-12345",
            is_active=True
        )
    
    def test_search_parts_with_api_key(self):
        response = self.client.get(
            "/api/external/parts/search/?query=Motor",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Motor V8"
        
        integration_log = IntegrationLog.objects.first()
        assert integration_log.action == "search_parts"
        assert integration_log.status == "success"
    
    def test_search_parts_without_api_key(self):
        response = self.client.get("/api/external/parts/search/?query=Motor")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_search_parts_with_invalid_api_key(self):
        response = self.client.get(
            "/api/external/parts/search/?query=Motor",
            HTTP_X_API_KEY="invalid-key"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_search_parts_with_inactive_api_key(self):
        self.api_key.is_active = False
        self.api_key.save()
        
        response = self.client.get(
            "/api/external/parts/search/?query=Motor",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_search_parts_without_query(self):
        response = self.client.get(
            "/api/external/parts/search/",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "query" in response.data["error"]


@pytest.mark.django_db
class TestExternalPartDetail:    
    def setup_method(self):
        self.client = APIClient()
        self.supplier = Supplier.objects.create(name="Fornecedor A")
        self.part = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10,
            supplier=self.supplier
        )
        self.api_key = ApiKey.objects.create(
            name="Test Key",
            key="test-key-12345",
            is_active=True
        )
    
    def test_get_part_detail_with_api_key(self):
        response = self.client.get(
            f"/api/external/parts/{self.part.id}/",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Motor V8"
        assert response.data["id"] == self.part.id
        
        integration_log = IntegrationLog.objects.first()
        assert integration_log.action == "get_part_detail"
        assert integration_log.status == "success"
    
    def test_get_part_detail_not_found(self):
        response = self.client.get(
            "/api/external/parts/999/",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        integration_log = IntegrationLog.objects.first()
        assert integration_log.status == "error"
        assert "not found" in integration_log.error_message.lower()


@pytest.mark.django_db
class TestExternalInventoryUpdate:    
    def setup_method(self):
        self.client = APIClient()
        self.supplier = Supplier.objects.create(name="Fornecedor A")
        self.part = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10,
            supplier=self.supplier
        )
        self.api_key = ApiKey.objects.create(
            name="Test Key",
            key="test-key-12345",
            is_active=True
        )
    
    def test_update_inventory_increase(self):
        data = {
            "part_id": self.part.id,
            "quantity_delta": 5
        }
        response = self.client.post(
            "/api/external/inventory/update/",
            data,
            format="json",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == 15
        
        self.part.refresh_from_db()
        assert self.part.quantity == 15
        
        integration_log = IntegrationLog.objects.first()
        assert integration_log.action == "update_inventory"
        assert integration_log.status == "success"
    
    def test_update_inventory_decrease(self):
        data = {
            "part_id": self.part.id,
            "quantity_delta": -3
        }
        response = self.client.post(
            "/api/external/inventory/update/",
            data,
            format="json",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == 7
        
        self.part.refresh_from_db()
        assert self.part.quantity == 7
    
    def test_update_inventory_negative(self):
        data = {
            "part_id": self.part.id,
            "quantity_delta": -20
        }
        response = self.client.post(
            "/api/external/inventory/update/",
            data,
            format="json",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "negativa" in response.data["error"].lower()
        
        self.part.refresh_from_db()
        assert self.part.quantity == 10
        
        integration_log = IntegrationLog.objects.first()
        assert integration_log.status == "error"
    
    def test_update_inventory_missing_params(self):
        data = {"part_id": self.part.id}
        response = self.client.post(
            "/api/external/inventory/update/",
            data,
            format="json",
            HTTP_X_API_KEY=self.api_key.key
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quantity_delta" in response.data["error"]
