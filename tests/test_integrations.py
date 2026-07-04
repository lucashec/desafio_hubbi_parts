import pytest
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.integrations.models import ApiKey, IntegrationLog
from apps.inventory.models import Part


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
class TestExternalInventoryUpdate:

    def setup_method(self):
        self.client = APIClient()
        self.part = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10,
        )
        self.api_key = ApiKey.objects.create(
            name="Test Key",
            key="test-key-12345",
            is_active=True,
        )

    def post(self, payload):
        return self.client.post(
            "/api/external/inventory/update/",
            payload,
            format="json",
            HTTP_X_API_KEY=self.api_key.key,
        )

    def test_update_inventory_success(self):
        payload = [
            {
                "part_id": self.part.id,
                "quantity": 15,
            }
        ]
        response = self.post(payload)
        assert response.status_code == status.HTTP_207_MULTI_STATUS
        assert response.data == {
            "updated": 1,
            "errors": 0,
            "not_found": [],
        }
        self.part.refresh_from_db()
        assert self.part.quantity == 15

        log = IntegrationLog.objects.get()

        assert log.action == "update_inventory"
        assert log.status == "success"
        assert log.response["old_quantity"] == 10
        assert log.response["new_quantity"] == 15

    def test_update_inventory_negative_quantity(self):
        payload = [
            {
                "part_id": self.part.id,
                "quantity": -5,
            }
        ]

        response = self.post(payload)

        assert response.status_code == status.HTTP_207_MULTI_STATUS

        assert response.data["updated"] == 0
        assert response.data["errors"] == 1

        self.part.refresh_from_db()
        assert self.part.quantity == 10

        log = IntegrationLog.objects.get()
        assert log.status == "error"
        assert "negativa" in log.error_message.lower()

    def test_update_inventory_missing_quantity(self):
        payload = [
            {
                "part_id": self.part.id,
            }
        ]

        response = self.post(payload)

        assert response.status_code == status.HTTP_207_MULTI_STATUS

        assert response.data["updated"] == 0
        assert response.data["errors"] == 1

        self.part.refresh_from_db()
        assert self.part.quantity == 10

        log = IntegrationLog.objects.get()
        assert log.status == "error"
        assert "quantity" in log.error_message

    def test_update_inventory_part_not_found(self):
        payload = [
            {
                "part_id": 9999,
                "quantity": 20,
            }
        ]

        response = self.post(payload)

        assert response.status_code == status.HTTP_207_MULTI_STATUS

        assert response.data["updated"] == 0
        assert response.data["errors"] == 1
        assert response.data["not_found"] == [
            {
                "part_id": 9999,
                "error": "Part not found",
            }
        ]

        log = IntegrationLog.objects.get()
        assert log.status == "error"

    def test_update_inventory_missing_part_id(self):
        payload = [
            {
                "quantity": 20,
            }
        ]

        response = self.post(payload)

        assert response.status_code == status.HTTP_207_MULTI_STATUS

        assert response.data["updated"] == 0
        assert response.data["errors"] == 1

        log = IntegrationLog.objects.get()
        assert log.status == "error"
        assert "part_id" in log.error_message

    def test_payload_must_be_list(self):
        payload = {
            "part_id": self.part.id,
            "quantity": 20,
        }

        response = self.post(payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "lista" in response.data["error"].lower()

    def test_update_multiple_parts(self):
        part2 = Part.objects.create(
            name="Filtro",
            price=Decimal("50.00"),
            quantity=5,
        )

        payload = [
            {
                "part_id": self.part.id,
                "quantity": 30,
            },
            {
                "part_id": part2.id,
                "quantity": 12,
            },
        ]

        response = self.post(payload)

        assert response.status_code == status.HTTP_207_MULTI_STATUS

        assert response.data == {
            "updated": 2,
            "errors": 0,
            "not_found": [],
        }

        self.part.refresh_from_db()
        part2.refresh_from_db()

        assert self.part.quantity == 30
        assert part2.quantity == 12

        assert IntegrationLog.objects.filter(status="success").count() == 2