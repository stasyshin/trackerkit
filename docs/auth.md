# Auth

## Signature
```python
TrackerClient(
    provider: str,
    auth_data: dict,
    connection_timeout: float = 3,
    max_retries: int = 0,
    relation_mapping: RelationMappingConfig | None = None,
)
await client.check_connection() -> bool
await client.ensure_connection() -> None
await client.get_connection_diagnostic() -> ConnectionDiagnostic
```

## Providers
- `jira`
- `yandex_tracker`
- `asana`

## Jira

### `auth_data`
- `base_url`: `str`
- `email`: `str | None`
- `api_token`: `str | None`
- `access_token`: `str | None`

### Validation
- required: `base_url`
- required: one of `api_token` or `access_token`
- `JiraClient` uses token auth only
- pass Jira token in `access_token` or `api_token`

### Example
```python
from depensee_tracker_client import TrackerClient

client = TrackerClient(
    provider="jira",
    auth_data={
        "base_url": "https://your-domain.atlassian.net",
        "access_token": "secret",
    },
    connection_timeout=3,
    max_retries=0,
)
```

## Yandex Tracker

### `auth_data`
- `token`: `str | None`
- `iam_token`: `str | None`
- `org_id`: `str | None`
- `cloud_org_id`: `str | None`

### Validation
- required: one of `token` or `iam_token`
- required: one of `org_id` or `cloud_org_id`

### Example
```python
from depensee_tracker_client import TrackerClient

client = TrackerClient(
    provider="yandex_tracker",
    auth_data={
        "token": "oauth-token",
        "org_id": "your-org-id",
    },
    connection_timeout=3,
)
```

## Asana

### `auth_data`
- `access_token`: `str`

### Validation
- required: `access_token`

### Example
```python
from depensee_tracker_client import TrackerClient

client = TrackerClient(
    provider="asana",
    auth_data={
        "access_token": "secret",
    },
    connection_timeout=3,
)
```

## Errors
- `ConfigurationError` if required auth fields are missing
- `AuthenticationError` if the client is disconnected or provider auth is invalid
- `ValueError` if `provider` is not supported

## Connection Options
- `connection_timeout` controls provider request timeout in seconds
- `max_retries` controls additional retry attempts for Jira transport
- `relation_mapping` overrides default relation normalization and provider link mapping
- these options are passed separately from `auth_data`
- defaults are defined on `TrackerClient`, not in environment variables
- current defaults: `connection_timeout=3`, `max_retries=0`

## Relation Mapping
- `RelationMappingConfig` is an optional runtime config for relation semantics
- by default:
  - Jira maps `relates` and `blocks` through issue links
  - Jira maps `contains` through structural hierarchy
  - Yandex Tracker maps `relates`, `blocks`, and `contains` through native link values
- pass a custom config only when provider defaults do not match your workspace setup

### Example
```python
from depensee_tracker_client import (
    JiraContainsMode,
    JiraLinkTypeMapping,
    JiraRelationMappingConfig,
    RelationMappingConfig,
    RelationType,
    TrackerClient,
)

relation_mapping = RelationMappingConfig(
    jira=JiraRelationMappingConfig(
        contains_mode=JiraContainsMode.HYBRID,
        contains_link_mappings=(
            JiraLinkTypeMapping(
                relation_type=RelationType.CONTAINS,
                type_name="Contains",
                outward_label="contains",
                inward_label="is contained by",
            ),
        ),
    )
)

client = TrackerClient(
    provider="jira",
    auth_data={
        "base_url": "https://your-domain.atlassian.net",
        "access_token": "secret",
    },
    relation_mapping=relation_mapping,
)
```

## Diagnostics
- `TrackerClient(...)` validates configuration immediately and raises `ConfigurationError` if required auth fields are missing
- provider network calls are lazy and usually start on `check_connection()` or the first business method call
- `check_connection()` returns only `bool`
- `ensure_connection()` writes a named library log entry on failure and raises a normalized domain error
- `get_connection_diagnostic()` returns structured connection details with `provider`, `is_connected`, `error_kind`, `error_type`, and `message`

## Connection Guard
- facade methods call `check_connection()` before provider operations
- if connection is invalid, the facade raises a normalized domain error based on the real diagnostic cause

## Internal Notes
- provider adapters are split into `transport`, `queries`, `mappers`, and `errors`
- the public `TrackerClient` facade stays thin and delegates to provider capabilities
- auth configs and shared DTOs remain `Pydantic` models
- the public API of the library is async
- provider transports may use native async clients or wrap sync SDKs internally
- the library itself does not read `.env`; configuration is injected from the host service
- local `examples/` may load `.env.example` and `.env` only for manual development runs
- auth credentials in examples are loaded with precedence: process environment -> `.env` -> `.env.example`

## Host Service Example
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

from depensee_tracker_client import TrackerClient


class TrackerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    jira_base_url: str
    jira_token: str


settings = TrackerSettings()

client = TrackerClient(
    provider="jira",
    auth_data={
        "base_url": settings.jira_base_url,
        "access_token": settings.jira_token,
    },
    connection_timeout=3,
    max_retries=0,
)
```
