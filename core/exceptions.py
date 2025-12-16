import logging

from django.db.models import ProtectedError
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)
EXCEPTIONS = {
    NotAuthenticated: {
        "response": {
            "detail": "Токен не предоставлен",
            "code": "not_authenticated",
        },
        "status": 401,
    },
    AuthenticationFailed: {
        "response": {
            "detail": "Неверные учетные данные",
            "code": "authentication_failed",
        },
        "status": 401,
    },
    TokenError: {
        "response": {
            "detail": "Ошибка токена",
            "code": "token_error",
        },
        "status": 401,
    },
    InvalidToken: {
        "response": {
            "detail": "Недействительный токен",
            "code": "invalid_token",
        },
        "status": 401,
    },
    ProtectedError: {
        "response": {
            "detail": "Защищено от удаление",
            "code": "protected_from_deletion",
        },
        "status": 403,
    },
    500: {
        "response": {
            "detail": "Внутренняя ошибка",
            "code": "internal_error",
        },
        "status": 500,
    },
}


def drf_exc_handler(exc, context):
    user_id = (
        context["request"].user.get("user_id")
        if isinstance(context["request"].user, dict)
        else None
    )
    logger.exception(
        f"[DRF Exc Handler] Ошибка: {exc} | User: {user_id}", exc_info=True
    )

    if response := exception_handler(exc, context):
        exception = EXCEPTIONS.get(type(exc), None)

        if exception:
            return Response(exception["response"], status=exception["status"])

        if not isinstance(response.data, dict):
            return Response(
                {"backend_error": "В исключениях можно использовать только dict"}
            )

        response.data["code"] = response.data.get(
            "code", getattr(exc, "default_code", response.status_code)
        )
        extra = getattr(exc, "extra", None)
        if extra:
            response.data["extra"] = extra
        return response
    else:
        exception = EXCEPTIONS.get(type(exc), EXCEPTIONS[500])
        return Response(exception["response"], status=exception["status"])


class DjExcHandlerMiddleware(MiddlewareMixin):
    def process_exception(self, request, exc):
        user_id = (
            request.user.get("user_id") if isinstance(request.user, dict) else None
        )
        logger.exception(
            f"[DJ Exc Handler] Ошибка: {exc} | User: {user_id}", exc_info=True
        )
        return Response(EXCEPTIONS[500]["response"], status=500)


class ConflictException(APIException):
    status_code = 409
    default_detail = "Произошла ошибка конфликта"
    default_code = "conflict"

    def __init__(self, detail=None, code=None):
        self.default_detail = detail if detail else self.default_detail
        self.default_code = code if code else self.default_code
        super().__init__()


class PermissionDeniedException(APIException):
    status_code = 403
    default_detail = "Доступ запрещен"
    default_code = "permission_denied"

    def __init__(self, detail=None, code=None):
        self.default_detail = detail if detail else self.default_detail
        self.default_code = code if code else self.default_code
        super().__init__()


class NotFoundException(APIException):
    status_code = 404
    default_detail = "Не найдено"
    default_code = "not_found"

    def __init__(self, detail=None, code=None):
        self.default_detail = detail if detail else self.default_detail
        self.default_code = code if code else self.default_code
        super().__init__()
