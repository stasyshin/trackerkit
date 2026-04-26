"""Unit tests for `domain.errors.get_error_kind` (POL-1)."""

from trackerkit.domain.enums import ConnectionErrorKind
from trackerkit.domain.errors import (
    AuthenticationError,
    ConfigurationError,
    ProviderCapabilityError,
    ProviderError,
    get_error_kind,
)


def test_authentication_maps_to_authentication_kind() -> None:
    assert get_error_kind(AuthenticationError("x")) is ConnectionErrorKind.AUTHENTICATION


def test_configuration_maps_to_configuration_kind() -> None:
    assert get_error_kind(ConfigurationError("x")) is ConnectionErrorKind.CONFIGURATION


def test_capability_maps_to_capability_kind() -> None:
    assert get_error_kind(ProviderCapabilityError("x")) is ConnectionErrorKind.CAPABILITY


def test_provider_error_maps_to_provider_kind() -> None:
    assert get_error_kind(ProviderError("x")) is ConnectionErrorKind.PROVIDER


def test_unknown_error_falls_back_to_provider_kind() -> None:
    assert get_error_kind(RuntimeError("x")) is ConnectionErrorKind.PROVIDER


def test_kind_string_value_is_stable_for_serialization() -> None:
    assert ConnectionErrorKind.AUTHENTICATION.value == "authentication"
    assert ConnectionErrorKind.CONFIGURATION.value == "configuration"
    assert ConnectionErrorKind.CAPABILITY.value == "capability"
    assert ConnectionErrorKind.PROVIDER.value == "provider"
