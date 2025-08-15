from typing import Callable

from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response

from .exceptions import ConflictException, PermissionDeniedException
from .models import Idempotency


def get_idempotency(path: str, key: str):
    return Idempotency.objects.filter(path=path, key=key).first()


def apply(
    path: str, key: str, request=None, response=None, help_data=None, commit=True
):
    idempotency = Idempotency(
        applied_at=now(),
        path=path,
        key=key,
        request=request,
        response=response,
        help_data=help_data,
    )

    if commit:
        idempotency.save()

    return idempotency


def get_not_applied_idempotency_keys(path, keys):
    applied_keys = list(
        Idempotency.objects.filter(path=path, key__in=keys).values_list(
            "key", flat=True
        )
    )
    return [key for key in keys if key not in applied_keys]


def rollback(idempotency: Idempotency):
    idempotency.rolled_back_at = now()
    idempotency.status = "rolled-back"
    idempotency.save(update_fields=["rolled_back_at", "status"])


def reapply(idempotency: Idempotency, request, response, help_data):
    idempotency.applied_at = now()
    idempotency.status = "applied"
    idempotency.request = request
    idempotency.response = response
    idempotency.help_data = help_data
    idempotency.save(
        update_fields=["applied_at", "status", "request", "response", "help_data"]
    )


def idempotency_required_view(view):
    def wrapper(request, *args, **kwargs):
        if not (idempotency_key := request.headers.get("Idempotency-Key", None)):
            raise PermissionDeniedException(
                "Set Idempotency-Key Header", "set_idempotency_key_header"
            )

        if request.method not in ["POST", "DELETE"]:
            raise MethodNotAllowed(method=request.method)

        with transaction.atomic():
            idempotency = get_idempotency(request.path, idempotency_key)

            if not idempotency:
                if request.method == "POST":
                    response = view(request, *args, **kwargs)
                    apply(
                        request.path,
                        idempotency_key,
                        request.data,
                        response.data,
                        getattr(request, "help_data", {}),
                    )
                    return response
                else:
                    raise ConflictException(
                        "Idempotency never applied before", "never_applied_idempotency"
                    )

            if idempotency.status == "applied" and request.method == "POST":
                return Response(idempotency.response, status=200)

            elif idempotency.status == "rolled-back" and request.method == "DELETE":
                return Response(idempotency.response, status=200)

            elif idempotency.status == "applied" and request.method == "DELETE":
                request._full_data = idempotency.request
                request.help_data = idempotency.help_data
                view(request, *args, **kwargs)
                rollback(idempotency)
                return Response(idempotency.response, status=200)

            else:  # rolled-back and POST
                response = view(request, *args, **kwargs)
                reapply(
                    idempotency,
                    request.data,
                    response.data,
                    getattr(request, "help_data", {}),
                )
                return response

    return wrapper


def idempotency_required_mq_consumer(consumer: Callable):
    def wrapper(data, idempotency_path, idempotency_key):
        idempotency = get_idempotency(idempotency_path, idempotency_key)

        if not idempotency:
            with transaction.atomic():
                consumer(data)
                apply(idempotency_path, idempotency_key)

    return wrapper
