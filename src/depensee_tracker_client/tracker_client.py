import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from depensee_tracker_client.contracts.task_tracker_client import TaskTrackerClient
from depensee_tracker_client.domain.enums import Provider
from depensee_tracker_client.domain.errors import AuthenticationError, ConfigurationError, ProviderError
from depensee_tracker_client.domain.models import (
    Comment,
    ConnectionDiagnostic,
    CreateCommentInput,
    CreateProjectInput,
    CreateRelationInput,
    CreateTaskInput,
    Project,
    Relation,
    Task,
    TaskQuery,
    UpdateProjectInput,
    UpdateTaskInput,
    User,
    Workspace,
)
from depensee_tracker_client.factory.client_factory import TaskTrackerClientFactory

T = TypeVar("T")
logger = logging.getLogger("depensee.tracker_client.client")


class TrackerClient:
    """Facade over provider-specific clients.

    One instance of this class works with one selected task tracker only.
    """

    def __init__(
        self,
        provider: Provider | str,
        auth_data: dict,
        connection_timeout: int = 3,
        max_retries: int = 0,
    ) -> None:
        """Create a facade client for one selected provider.

        `auth_data` is provider-specific:
        - `jira`: `base_url` and exactly one of `access_token` or `api_token`
        - `yandex_tracker`: exactly one of `token` or `iam_token`, and exactly
          one of `org_id` or `cloud_org_id`
        - `asana`: `access_token`
        """

        self._provider = Provider(provider)
        config_data = {
            **auth_data,
            "timeout_seconds": connection_timeout,
        }
        if self._provider is Provider.JIRA:
            config_data["max_retries"] = max_retries

        self._auth_config = TaskTrackerClientFactory.build_auth_config(
            self._provider,
            config_data,
        )
        self._client: TaskTrackerClient = TaskTrackerClientFactory.create(
            self._auth_config
        )

    @property
    def provider(self) -> Provider:
        return self._provider

    def _build_connection_error(
        self,
        diagnostic: ConnectionDiagnostic,
    ) -> AuthenticationError | ConfigurationError | ProviderError:
        message = (
            diagnostic.message
            or f"Provider '{self._provider.value}' connection check failed."
        )

        if diagnostic.error_kind == "authentication":
            return AuthenticationError(message)

        if diagnostic.error_kind == "configuration":
            return ConfigurationError(message)

        return ProviderError(message)

    async def _ensure_connection(self) -> None:
        diagnostic = await self.get_connection_diagnostic()
        if not diagnostic.is_connected:
            logger.warning(
                "Provider connection check failed: provider=%s kind=%s type=%s message=%s",
                self._provider.value,
                diagnostic.error_kind or "unknown",
                diagnostic.error_type or "unknown",
                diagnostic.message or "no details",
            )
            raise self._build_connection_error(diagnostic)

    async def _execute(self, operation: Callable[[], Awaitable[T]]) -> T:
        await self._ensure_connection()
        return await operation()

    async def check_connection(self) -> bool:
        diagnostic = await self.get_connection_diagnostic()
        return diagnostic.is_connected

    async def ensure_connection(self) -> None:
        await self._ensure_connection()

    async def get_connection_diagnostic(self) -> ConnectionDiagnostic:
        return await self._client.get_connection_diagnostic()

    async def get_task(self, task_id: str) -> Task:
        return await self._execute(lambda: self._client.get_task(task_id))

    async def list_tasks(self, query: TaskQuery | None = None) -> list[Task]:
        return await self._execute(lambda: self._client.list_tasks(query))

    async def create_task(self, payload: CreateTaskInput) -> Task:
        return await self._execute(lambda: self._client.create_task(payload))

    async def update_task(self, task_id: str, payload: UpdateTaskInput) -> Task:
        return await self._execute(lambda: self._client.update_task(task_id, payload))

    async def delete_task(self, task_id: str) -> None:
        await self._execute(lambda: self._client.delete_task(task_id))

    async def list_workspaces(self) -> list[Workspace]:
        return await self._execute(self._client.list_workspaces)

    async def get_project(self, project_id: str) -> Project:
        return await self._execute(lambda: self._client.get_project(project_id))

    async def list_projects(self, workspace_id: str | None = None) -> list[Project]:
        return await self._execute(lambda: self._client.list_projects(workspace_id))

    async def create_project(self, payload: CreateProjectInput) -> Project:
        return await self._execute(lambda: self._client.create_project(payload))

    async def update_project(
        self,
        project_id: str,
        payload: UpdateProjectInput,
    ) -> Project:
        return await self._execute(
            lambda: self._client.update_project(project_id, payload)
        )

    async def delete_project(self, project_id: str) -> None:
        await self._execute(lambda: self._client.delete_project(project_id))

    async def list_users(self) -> list[User]:
        return await self._execute(self._client.list_users)

    async def list_comments(self, task_id: str) -> list[Comment]:
        return await self._execute(lambda: self._client.list_comments(task_id))

    async def create_comment(self, payload: CreateCommentInput) -> Comment:
        return await self._execute(lambda: self._client.create_comment(payload))

    async def list_relations(self, task_id: str) -> list[Relation]:
        return await self._execute(lambda: self._client.list_relations(task_id))

    async def create_relation(self, payload: CreateRelationInput) -> Relation:
        return await self._execute(lambda: self._client.create_relation(payload))

    async def delete_relation(self, relation_id: str) -> None:
        await self._execute(lambda: self._client.delete_relation(relation_id))

