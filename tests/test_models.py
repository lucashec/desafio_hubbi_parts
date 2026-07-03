import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.inventory.models import Part
from apps.consultant.models import ConsultantQuery, ConsultantResponse
from apps.integrations.models import ApiKey, IntegrationLog


User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Testes para o modelo User."""

    def test_create_user(self):
        """Testa criação de usuário."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active

    def test_user_str_representation(self):
        """Testa representação em string do usuário."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        assert str(user) == "test@example.com"

    def test_user_get_full_name(self):
        """Testa obtenção do nome completo."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )
        assert user.get_full_name() == "John Doe"

    def test_user_is_admin(self):
        """Testa se usuário é admin."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        assert not user.is_admin()
        assert admin_user.is_admin()


@pytest.mark.django_db
class TestPartModel:
    """Testes para o modelo Part."""

    def test_create_part(self):
        """Testa criação de peça."""
        part = Part.objects.create(
            name="Motor V8",
            description="Motor V8 3.0L",
            price=Decimal("5000.00"),
            quantity=10
        )
        assert part.name == "Motor V8"
        assert part.quantity == 10

    def test_part_is_available(self):
        """Testa disponibilidade da peça."""
        part_available = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10
        )
        part_unavailable = Part.objects.create(
            name="Turbo",
            price=Decimal("3000.00"),
            quantity=0
        )
        assert part_available.is_available()
        assert not part_unavailable.is_available()

    def test_part_get_display_price(self):
        """Testa formatação do preço."""
        part = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10
        )
        assert part.get_display_price() == "R$ 5000.00"

    def test_part_str_representation(self):
        """Testa representação em string."""
        part = Part.objects.create(
            name="Motor V8",
            price=Decimal("5000.00"),
            quantity=10
        )
        assert str(part) == "Motor V8"


@pytest.mark.django_db
class TestConsultantQueryModel:
    """Testes para o modelo ConsultantQuery."""

    def test_create_consultant_query(self):
        """Testa criação de query."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        query = ConsultantQuery.objects.create(
            user=user,
            query_text="Preciso de um motor para meu carro"
        )
        assert query.query_text == "Preciso de um motor para meu carro"
        assert query.status == "pending"

    def test_consultant_query_is_completed(self):
        """Testa status de conclusão."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        query = ConsultantQuery.objects.create(
            user=user,
            query_text="Teste",
            status="pending"
        )
        assert not query.is_completed()
        query.status = "completed"
        assert query.is_completed()


@pytest.mark.django_db
class TestConsultantResponseModel:
    """Testes para o modelo ConsultantResponse."""

    def test_create_consultant_response(self):
        """Testa criação de resposta."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        query = ConsultantQuery.objects.create(
            user=user,
            query_text="Teste"
        )
        response = ConsultantResponse.objects.create(
            query=query,
            response_text="Recomendo o motor X",
            tokens_used=150
        )
        assert response.tokens_used == 150

    def test_consultant_response_processing_time_formatted(self):
        """Testa formatação do tempo de processamento."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        query = ConsultantQuery.objects.create(
            user=user,
            query_text="Teste"
        )
        response = ConsultantResponse.objects.create(
            query=query,
            response_text="Teste",
            processing_time=1.234
        )
        assert response.get_processing_time_formatted() == "1.23s"


@pytest.mark.django_db
class TestApiKeyModel:
    """Testes para o modelo ApiKey."""

    def test_create_api_key(self):
        """Testa criação de API Key."""
        api_key = ApiKey.objects.create(
            name="ERP System",
            description="Integração com ERP"
        )
        assert api_key.name == "ERP System"
        assert api_key.is_active

    def test_api_key_is_valid(self):
        """Testa se API Key é válida."""
        api_key_active = ApiKey.objects.create(
            name="ERP System",
            is_active=True
        )
        api_key_inactive = ApiKey.objects.create(
            name="WMS System",
            is_active=False
        )
        assert api_key_active.is_valid()
        assert not api_key_inactive.is_valid()

    def test_api_key_get_masked_key(self):
        """Testa mascaramento da chave."""
        api_key = ApiKey.objects.create(
            name="Test",
            key="1234567890abcdef"
        )
        masked = api_key.get_masked_key()
        assert masked.startswith("1234")
        assert masked.endswith("cdef")
        assert "..." in masked


@pytest.mark.django_db
class TestIntegrationLogModel:
    """Testes para o modelo IntegrationLog."""

    def test_create_integration_log(self):
        """Testa criação de log de integração."""
        api_key = ApiKey.objects.create(name="ERP System")
        log = IntegrationLog.objects.create(
            api_key=api_key,
            action="stock_update",
            status="success"
        )
        assert log.action == "stock_update"
        assert log.status == "success"

    def test_integration_log_is_successful(self):
        """Testa sucesso da integração."""
        api_key = ApiKey.objects.create(name="ERP System")
        log_success = IntegrationLog.objects.create(
            api_key=api_key,
            action="test",
            status="success"
        )
        log_error = IntegrationLog.objects.create(
            api_key=api_key,
            action="test",
            status="error"
        )
        assert log_success.is_successful()
        assert not log_error.is_successful()

    def test_integration_log_processing_time_formatted(self):
        """Testa formatação do tempo de processamento."""
        api_key = ApiKey.objects.create(name="ERP System")
        log = IntegrationLog.objects.create(
            api_key=api_key,
            action="test",
            status="success",
            processing_time=2.567
        )
        assert log.get_processing_time_formatted() == "2.57s"
