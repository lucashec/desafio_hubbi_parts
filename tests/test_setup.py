import pytest
from django.conf import settings


class TestProjectSetup:
    """
    Testes para validar a configuração do projeto.
    """

    def test_django_settings_configured(self):
        """Verifica se o Django está configurado."""
        assert settings.DEBUG is not None

    def test_installed_apps(self):
        """Verifica se as aplicações foram registradas."""
        assert "rest_framework" in settings.INSTALLED_APPS
        assert "apps.accounts" in settings.INSTALLED_APPS
        assert "apps.inventory" in settings.INSTALLED_APPS
        assert "apps.consultant" in settings.INSTALLED_APPS
        assert "apps.integrations" in settings.INSTALLED_APPS

    def test_database_configured(self):
        """Verifica se o banco de dados está configurado."""
        assert settings.DATABASES["default"]["ENGINE"] is not None

    def test_redis_url_exists(self):
        """Verifica se o Redis está configurado."""
        assert settings.REDIS_URL is not None

    def test_celery_configured(self):
        """Verifica se o Celery está configurado."""
        assert settings.CELERY_BROKER_URL is not None
        assert settings.CELERY_RESULT_BACKEND is not None

    def test_jwt_configured(self):
        """Verifica se o JWT está configurado."""
        assert "rest_framework_simplejwt" in settings.INSTALLED_APPS

    @pytest.mark.django_db
    def test_user_model_available(self):
        """Verifica se o modelo de usuário está disponível."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assert User is not None

    @pytest.mark.django_db
    def test_part_model_available(self):
        """Verifica se o modelo de peça está disponível."""
        from apps.inventory.models import Part
        assert Part is not None

    @pytest.mark.django_db
    def test_api_key_model_available(self):
        """Verifica se o modelo de API Key está disponível."""
        from apps.integrations.models import ApiKey
        assert ApiKey is not None
