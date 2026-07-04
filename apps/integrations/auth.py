from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import ApiKey
from django.utils import timezone


class APIKeyUser:
    def __init__(self, api_key):
        self.api_key = api_key
        self.is_authenticated = True
        self.username = f"api_key_{api_key.id}"
    
    def __str__(self):
        return self.username


class ApiKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            raise AuthenticationFailed("API key não encontrada") 
        
        try:
            key_obj = ApiKey.objects.get(key=api_key)
        except ApiKey.DoesNotExist:
            raise AuthenticationFailed('API Key inválida ou não encontrada')
        
        if not key_obj.is_valid():
            raise AuthenticationFailed('API Key está desativada')
        
        key_obj.last_used_at = timezone.now()
        key_obj.save(update_fields=['last_used_at'])
        
        user = APIKeyUser(key_obj)
        return (user, key_obj)
    
    def authenticate_header(self, request):
        return 'X-API-Key'

