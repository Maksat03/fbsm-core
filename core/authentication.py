import jwt
from django.conf import settings

from django.contrib.auth.models import AnonymousUser
from drf_spectacular.extensions import OpenApiAuthenticationExtension

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication


class StatelessJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "core.authentication.StatelessJWTAuthentication"
    name = "JWTAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }


class StatelessJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Срок действия токена истёк")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Неверный токен")

        return payload, None


class ServiceAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "core.authentication.ServiceAuthentication"
    name = "ServiceAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-KEY",
        }


class ServiceAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if not (token := request.headers.get("X-API-KEY")):
            return None

        if token != settings.SERVICE_API_KEY:
            raise AuthenticationFailed("Неверный X-API-KEY")

        return AnonymousUser(), None
