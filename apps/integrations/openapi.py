from drf_spectacular.extensions import OpenApiAuthenticationExtension
from .auth import ApiKeyAuthentication


class ApiKeyAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = ApiKeyAuthentication
    name = 'ApiKeyAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-KEY',
            'description': 'API Key authentication'
        }
