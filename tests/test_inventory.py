import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.inventory.models import Part, Supplier


User = get_user_model()


@pytest.mark.django_db
class TestPartViewSet:
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
        self.supplier = Supplier.objects.create(name="Fornecedor A")
        self.part_data = {
            "name": "Motor V8",
            "description": "Motor V8 3.0L",
            "price": "5000.00",
            "quantity": 10,
            "supplier": self.supplier.id,
        }

    def test_list_parts_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/parts/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_parts_unauthenticated(self):
        response = self.client.get("/api/parts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_part_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/parts/", self.part_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Motor V8"

    def test_create_part_non_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/parts/", self.part_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_part(self):
        part = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10,
            supplier=self.supplier
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/parts/{part.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Motor V8"

    def test_update_part_admin(self):
        part = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10,
            supplier=self.supplier
        )
        self.client.force_authenticate(user=self.admin)
        data = {"quantity": 20}
        response = self.client.patch(f"/api/parts/{part.id}/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == 20

    def test_delete_part_admin(self):
        part = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10,
            supplier=self.supplier
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/parts/{part.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Part.objects.filter(id=part.id).exists()

    def test_available_parts(self):
        Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10,
            supplier=self.supplier
        )
        Part.objects.create(
            name="Turbo",
            price=Decimal("3000.00"),
            quantity=0,
            supplier=self.supplier
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/parts/available/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Motor V8"

    def test_search_parts(self):
        Part.objects.create(
            name="Motor V8",
            description="Motor potente",
            price=Decimal("5000.00"),
            quantity=10,
            supplier=self.supplier
        )
        Part.objects.create(
            name="Turbo",
            description="Turbo kompressor",
            price=Decimal("3000.00"),
            quantity=5,
            supplier=self.supplier
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/parts/?search=Motor")
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]["name"] == "Motor V8"


@pytest.mark.django_db
class TestSupplierViewSet:
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

    def test_list_suppliers(self):
        Supplier.objects.create(name="Fornecedor A")
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/suppliers/")
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_create_supplier_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "Novo Fornecedor",
            "catalog_url": "https://example.com/catalog"
        }
        response = self.client.post("/api/suppliers/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_supplier_non_admin(self):
        self.client.force_authenticate(user=self.user)
        data = {"name": "Novo Fornecedor"}
        response = self.client.post("/api/suppliers/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
