from typing import Sequence

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import serializers
from rest_framework.exceptions import APIException

default_description = (
    "**Ошибки по Use-Cases приведены в разделе Responses**\n\n"
    "**Ошибки по умолчанию (401, 403, 500):**\n\n"
    '`{ "detail": "error\'s text", "code": "error\'s code" }`\n\n'
)


def schema(schema_class):
    def decorator(view):
        schema_params = {
            key: value
            for key, value in schema_class.__dict__.items()
            if not key.startswith("__")
        }

        schema_params["request"] = schema_params.get("request", None)
        schema_params["description"] = (
            schema_params.get("description", "") + "\n\n" + default_description
        )

        return extend_schema(**schema_params)(view)

    return decorator


class SuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)


class BadRequestResponseSerializer(serializers.Serializer):
    field_name1 = serializers.ListField(
        child=serializers.CharField(default="Текст ошибки payload input field 1")
    )
    field_name2 = serializers.ListField(
        child=serializers.CharField(default="Текст ошибки payload input field 2")
    )
    code = serializers.CharField(default="invalid")


class SimpleExceptionResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField()


class SimpleExceptionResponses:
    def __init__(self, exceptions: Sequence[APIException]):
        self.exceptions = exceptions

    @property
    def schema(self):
        exception_examples: list[OpenApiExample] = []
        for exception in self.exceptions:
            default_extra = getattr(exception, "default_extra", None)
            value = {
                "detail": exception.default_detail,
                "code": exception.default_code,
            }
            if default_extra:
                value["extra"] = default_extra
            exception_examples.append(
                OpenApiExample(
                    name=exception.default_detail,
                    response_only=True,
                    value=value,
                )
            )
        return OpenApiResponse(
            response=SimpleExceptionResponseSerializer,
            examples=exception_examples,
        )


IdempotencyKeyHeaderSchema = OpenApiParameter(
    name="Idempotency-Key",
    type=str,
    location=OpenApiParameter.HEADER,
    description="Ключ идемпотентности для предотвращения повторных операций",
)
