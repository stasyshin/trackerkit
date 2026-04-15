from yandex_tracker_client import exceptions as yandex_exceptions

from depensee_tracker_client.domain.errors import AuthenticationError, ProviderError


def raise_yandex_error(error: Exception) -> None:
    if isinstance(error, yandex_exceptions.Forbidden):
        raise AuthenticationError(str(error)) from error

    if isinstance(error, yandex_exceptions.TrackerServerError):
        raise ProviderError(str(error)) from error

    if isinstance(error, yandex_exceptions.TrackerRequestError):
        raise ProviderError(str(error)) from error

    raise error

