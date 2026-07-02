import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status


User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationViews:
    """Testes para views de autenticação."""

    def setup_method(self):
        """Setup antes de cada teste."""
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.token_url = "/api/token/"
        self.refresh_url = "/api/token/refresh/"
        self.profile_url = "/api/auth/profile/"
        self.logout_url = "/api/auth/logout/"

    def test_user_registration_success(self):
        """Testa registro com sucesso."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = self.client.post(self.register_url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == "newuser@example.com"

    def test_user_registration_password_mismatch(self):
        """Testa registro com senhas diferentes."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "password_confirm": "differentpass123",
        }
        response = self.client.post(self.register_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_user_registration_duplicate_username(self):
        """Testa registro com username duplicado."""
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="pass123"
        )
        data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        response = self.client.post(self.register_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_user_registration_duplicate_email(self):
        """Testa registro com email duplicado."""
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="pass123"
        )
        data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        response = self.client.post(self.register_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_user_registration_short_password(self):
        """Testa registro com senha muito curta."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "short",
            "password_confirm": "short",
        }
        response = self.client.post(self.register_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self):
        """Testa login com sucesso."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post(self.token_url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_credentials(self):
        """Testa login com credenciais inválidas."""
        User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        data = {
            "username": "testuser",
            "password": "wrongpass"
        }
        response = self.client.post(self.token_url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self):
        """Testa refresh de token."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Obter tokens
        response = self.client.post(
            self.token_url,
            {"username": "testuser", "password": "testpass123"},
            format="json"
        )
        refresh_token = response.data["refresh"]

        # Usar refresh token
        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_get_profile_unauthenticated(self):
        """Testa obtenção de perfil sem autenticação."""
        response = self.client.get(self.profile_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout(self):
        """Testa logout."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Login
        response = self.client.post(
            self.token_url,
            {"username": "testuser", "password": "testpass123"},
            format="json"
        )
        access_token = response.data["access"]

        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.post(
            self.logout_url,
            {},
            format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_token_contains_user_info(self):
        """Testa se token contém informações do usuário."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        response = self.client.post(
            self.token_url,
            {"username": "testuser", "password": "testpass123"},
            format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
