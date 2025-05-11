from django.db import transaction
from django.utils.timezone import now

from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed

from .models import Idempotency
from .exceptions import ConflictException, PermissionDeniedException


def _get_idempotency(path, key):
    return Idempotency.objects.filter(path=path, key=key).first()


def _apply(path, key, request=None, response=None, help_data=None):
    Idempotency.objects.create(
        applied_at=now(),
        path=path,
        key=key,
        request=request,
        response=response,
        help_data=help_data
    )


def _rollback(idempotency):
    idempotency.rolled_back_at = now()
    idempotency.status = "rolled-back"
    idempotency.save(update_fields=["rolled_back_at", "status"])


def _reapply(idempotency, request, response, help_data):
    idempotency.applied_at = now()
    idempotency.status = "applied"
    idempotency.request = request
    idempotency.response = response
    idempotency.help_data = help_data
    idempotency.save(update_fields=["applied_at", "status", "request", "response", "help_data"])


def idempotency_required_view(view):
    def wrapper(request, *args, **kwargs):
        if not (idempotency_key := request.headers.get("Idempotency-Key", None)):
            raise PermissionDeniedException("Set Idempotency-Key Header", "set_idempotency_key_header")

        if request.method not in ["POST", "DELETE"]:
            raise MethodNotAllowed(method=request.method)

        with transaction.atomic():
            idempotency = _get_idempotency(request.path, idempotency_key)

            if not idempotency:
                if request.method == "POST":
                    response = view(request, *args, **kwargs)
                    _apply(request.path, idempotency_key, request.data, response.data, getattr(request, "help_data", {}))
                    return response
                else:
                    raise ConflictException("Idempotency never applied before", "never_applied_idempotency")

            if idempotency.status == "applied" and request.method == "POST":
                return Response(idempotency.response, status=200)

            elif idempotency.status == "rolled-back" and request.method == "DELETE":
                return Response(idempotency.response, status=200)

            elif idempotency.status == "applied" and request.method == "DELETE":
                request._full_data = idempotency.request
                request.help_data = idempotency.help_data
                view(request, *args, **kwargs)
                _rollback(idempotency)
                return Response(idempotency.response, status=200)

            else:  # rolled-back and POST
                response = view(request, *args, **kwargs)
                _reapply(idempotency, request.data, response.data, getattr(request, "help_data", {}))
                return response

    return wrapper


def idempotency_required_mq_consumer(consumer):
    def wrapper(data, idempotency_path, idempotency_key):
        idempotency = _get_idempotency(idempotency_path, idempotency_key)

        if not idempotency:
            with transaction.atomic():
                consumer(data)
                _apply(idempotency_path, idempotency_key)

    return wrapper
