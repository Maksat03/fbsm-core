import logging

import pybreaker
import tenacity
from pybreaker import CircuitBreakerError
from requests.exceptions import ConnectionError, HTTPError, Timeout
from tenacity import RetryError

logger = logging.getLogger(__name__)

base_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=5 * 3,
    reset_timeout=90,
    exclude=[lambda e: not isinstance(e, (Timeout, ConnectionError, MS5xxError))],
)

base_retry = tenacity.retry(
    retry=tenacity.retry_if_exception_type((Timeout, ConnectionError)),
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=0.5, min=0.5, max=5),
    reraise=True,
)


class MS5xxError(Exception):
    def __init__(self, response):
        self.response = response
        self.message = "Internal Server Error"
        super().__init__(self.message)


def _safe_raise_exception(exc, request_name, saga_func, saga_args, raise_exception):
    if isinstance(exc, HTTPError):
        if 500 <= exc.response.status_code < 600:
            exc = MS5xxError(exc.response)

    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    text = getattr(response, "text", None)
    url = getattr(response, "url", None)
    method = getattr(getattr(response, "request", None), "method", None)

    logger.error(
        msg=(
            "\n\n\n"
            f"[Safe Request Error]"
            f"\nRequest Name: {request_name}"
            f"\nRequest Method: {method}"
            f"\nRequest URL: {url}"
            f"\nException Name: {type(exc).__name__}"
            f"\nException: {exc}"
            f"\nResponse Code: {status_code}"
            f"\nResponse Text: {text}"
            "\n\n\n"
        ),
        exc_info=True,
    )

    if saga_func and saga_args:
        try:
            saga_func(*saga_args, exc=exc)
        except Exception as e:
            logger.critical(
                f"[SAGA] Ошибка при выполнений {saga_func.__name__}: {e}", exc_info=True
            )
            raise e

    if raise_exception:
        raise exc


def safe_request(retry=base_retry, circuit_breaker=base_circuit_breaker):
    """
    Note:
    1. in your function, you must use response.raise_for_status()
    2. saga func is just void function, just executes if set a function
    3. if raise_exception is True, then exception will be raised if any, if it's False, nothing raises
    4. if you want you can don't use saga func and just add try/except block in your code where you call your func
    5. never touch this safe_request.py file, if it needed to be changed, notify me
    6. errors which can be raised are written here (below)
    """

    def decorator(request):
        def wrapper(
            *args, saga_func=None, saga_args=None, raise_exception=True, **kwargs
        ):
            @circuit_breaker(name=request.__name__)
            def inner():
                return request(*args, **kwargs)

            try:
                return retry(inner)()
            except RetryError as e:
                _safe_raise_exception(
                    e.last_attempt.exception(),
                    request.__name__,
                    saga_func,
                    saga_args,
                    raise_exception,
                )
            except (
                Timeout,
                ConnectionError,
                HTTPError,
                CircuitBreakerError,
                Exception,
            ) as e:
                _safe_raise_exception(
                    e, request.__name__, saga_func, saga_args, raise_exception
                )

        return wrapper

    return decorator
