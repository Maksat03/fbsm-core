import requests

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from rest_framework import permissions
from core.safe_request import safe_request


@safe_request()
def _check_seller_confirmation(seller_account_id):
    url = f"{settings.USER_SERVICE_URL}v1/sellers/{seller_account_id}/is-activated/"
    headers = {
        "X-API-KEY": settings.USER_SERVICE_API_KEY
    }

    response = requests.get(url, headers=headers, timeout=3)
    response.raise_for_status()
    return response.json()["is_activated"]


class IsGuestOrClient(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        return request.user["role"] == "guest" or request.user["role"] == "client"


class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        return request.user["role"] == "client"


class IsSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        return request.user["role"] == "seller"


class IsConfirmedSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        if request.user["role"] != "seller":
            return False

        return _check_seller_confirmation(request.user["user_id"])


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        return request.user["role"] == "super_admin"


class IsMicroservice(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.headers.get("X-API-KEY")
