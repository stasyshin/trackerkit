from trackerkit.domain.errors import AuthenticationError, ProviderError


def raise_asana_error(error: Exception) -> None:
    message = str(error)
    lowered = message.lower()

    if "unauthorized" in lowered or "forbidden" in lowered or "not authorized" in lowered:
        raise AuthenticationError(message) from error

    raise ProviderError(message) from error

