class TrackerClientError(Exception):
    """Base exception for the package."""


class ConfigurationError(TrackerClientError):
    """Raised when client configuration is invalid."""


class AuthenticationError(TrackerClientError):
    """Raised when provider authentication fails."""


class ProviderError(TrackerClientError):
    """Raised when a provider-specific operation fails."""


class ProviderCapabilityError(TrackerClientError):
    """Raised when a provider does not support a requested capability."""


TrackerKitError = TrackerClientError


def get_error_kind(error: Exception) -> str:
    if isinstance(error, AuthenticationError):
        return "authentication"
    if isinstance(error, ConfigurationError):
        return "configuration"
    if isinstance(error, ProviderCapabilityError):
        return "capability"
    if isinstance(error, ProviderError):
        return "provider"
    return "provider"

