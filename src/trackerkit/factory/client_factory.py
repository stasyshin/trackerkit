from trackerkit.contracts.auth import (
    AsanaAuthConfig,
    JiraAuthConfig,
    ProviderAuthConfig,
    YandexTrackerAuthConfig,
)
from trackerkit.contracts.task_tracker_client import TaskTrackerClient
from trackerkit.domain.enums import Provider
from trackerkit.domain.errors import ConfigurationError
from trackerkit.domain.relation_mapping import RelationMappingConfig
from trackerkit.providers.asana.client import AsanaClient
from trackerkit.providers.jira.client import JiraClient
from trackerkit.providers.yandex_tracker.client import YandexTrackerClient


class TaskTrackerClientFactory:
    _config_registry: dict[Provider, type[ProviderAuthConfig]] = {
        Provider.JIRA: JiraAuthConfig,
        Provider.YANDEX_TRACKER: YandexTrackerAuthConfig,
        Provider.ASANA: AsanaAuthConfig,
    }

    _client_registry: dict[Provider, type[TaskTrackerClient]] = {
        Provider.JIRA: JiraClient,
        Provider.YANDEX_TRACKER: YandexTrackerClient,
        Provider.ASANA: AsanaClient,
    }

    @staticmethod
    def create(
        config: ProviderAuthConfig,
        relation_mapping: RelationMappingConfig | None = None,
    ) -> TaskTrackerClient:
        config_type = TaskTrackerClientFactory._config_registry.get(config.provider)
        client_type = TaskTrackerClientFactory._client_registry.get(config.provider)

        if config_type is None or client_type is None:
            raise ConfigurationError(f"Unsupported provider: {config.provider}")

        if not isinstance(config, config_type):
            raise ConfigurationError(
                f"Expected {config_type.__name__} for provider {config.provider.value}."
            )

        if relation_mapping is None:
            return client_type(config)
        return client_type(config, relation_mapping=relation_mapping)

    @staticmethod
    def build_auth_config(
        provider: Provider | str, auth_data: dict
    ) -> ProviderAuthConfig:
        normalized_provider = Provider(provider)
        config_type = TaskTrackerClientFactory._config_registry.get(normalized_provider)

        if config_type is None:
            raise ConfigurationError(f"Unsupported provider: {provider}")

        return config_type(**auth_data)

