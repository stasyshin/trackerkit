import asyncio
from typing import Any

from asana import ApiClient, Configuration
from asana.api.projects_api import ProjectsApi
from asana.api.tasks_api import TasksApi
from asana.api.workspaces_api import WorkspacesApi

from depensee_tracker_client.contracts.auth import AsanaAuthConfig
from depensee_tracker_client.domain.enums import Provider
from depensee_tracker_client.domain.errors import get_error_kind
from depensee_tracker_client.domain.models import ConnectionDiagnostic
from depensee_tracker_client.providers.asana.errors import raise_asana_error


class AsanaTransport:
    def __init__(self, config: AsanaAuthConfig) -> None:
        self._config = config
        self._api_client: ApiClient | None = None
        self._projects_api: ProjectsApi | None = None
        self._tasks_api: TasksApi | None = None
        self._workspaces_api: WorkspacesApi | None = None

    def _opts_with_timeout(self, **kwargs: Any) -> dict[str, Any]:
        return {
            **kwargs,
            "_request_timeout": self._config.timeout_seconds,
        }

    def _ensure_apis(self) -> None:
        if self._api_client is not None:
            return

        configuration = Configuration()
        configuration.access_token = self._config.access_token
        self._api_client = ApiClient(configuration)
        self._projects_api = ProjectsApi(self._api_client)
        self._tasks_api = TasksApi(self._api_client)
        self._workspaces_api = WorkspacesApi(self._api_client)

    @property
    def projects(self) -> ProjectsApi:
        self._ensure_apis()
        assert self._projects_api is not None
        return self._projects_api

    @property
    def tasks(self) -> TasksApi:
        self._ensure_apis()
        assert self._tasks_api is not None
        return self._tasks_api

    @property
    def workspaces(self) -> WorkspacesApi:
        self._ensure_apis()
        assert self._workspaces_api is not None
        return self._workspaces_api

    async def _run(self, func, /, *args, **kwargs):
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as error:
            raise_asana_error(error)

    async def check_connection(self, workspace_fields: str) -> bool:
        diagnostic = await self.get_connection_diagnostic(workspace_fields)
        return diagnostic.is_connected

    async def get_connection_diagnostic(
        self,
        workspace_fields: str,
    ) -> ConnectionDiagnostic:
        try:
            await self._run(
                self.workspaces.get_workspaces,
                self._opts_with_timeout(limit=1, opt_fields=workspace_fields),
            )
        except Exception as error:
            return ConnectionDiagnostic(
                provider=Provider.ASANA,
                is_connected=False,
                error_kind=get_error_kind(error),
                message=str(error),
                error_type=type(error).__name__,
            )
        return ConnectionDiagnostic(
            provider=Provider.ASANA,
            is_connected=True,
        )

    async def get_task(self, task_id: str, task_fields: str) -> dict[str, Any]:
        return await self._run(
            self.tasks.get_task,
            task_id,
            self._opts_with_timeout(opt_fields=task_fields),
        )

    async def get_tasks_for_project(
        self,
        project_id: str,
        task_fields: str,
    ) -> list[dict[str, Any]]:
        return await self._run(
            self.tasks.get_tasks_for_project,
            project_id,
            self._opts_with_timeout(opt_fields=task_fields),
        )

    async def create_task(self, body: dict[str, Any], task_fields: str) -> dict[str, Any]:
        return await self._run(
            self.tasks.create_task,
            body,
            self._opts_with_timeout(opt_fields=task_fields),
        )

    async def update_task(
        self,
        task_id: str,
        body: dict[str, Any],
        task_fields: str,
    ) -> dict[str, Any]:
        return await self._run(
            self.tasks.update_task,
            body,
            task_id,
            self._opts_with_timeout(opt_fields=task_fields),
        )

    async def delete_task(self, task_id: str) -> None:
        await self._run(
            self.tasks.delete_task,
            task_id,
            _request_timeout=self._config.timeout_seconds,
        )

    async def get_workspaces(self, workspace_fields: str) -> list[dict[str, Any]]:
        return await self._run(
            self.workspaces.get_workspaces,
            self._opts_with_timeout(limit=100, opt_fields=workspace_fields),
        )

    async def get_project(self, project_id: str, project_fields: str) -> dict[str, Any]:
        return await self._run(
            self.projects.get_project,
            project_id,
            self._opts_with_timeout(opt_fields=project_fields),
        )

    async def get_projects(
        self,
        workspace_id: str | None,
        project_fields: str,
    ) -> list[dict[str, Any]]:
        opts = self._opts_with_timeout(limit=100, opt_fields=project_fields)
        if workspace_id is not None:
            return await self._run(
                self.projects.get_projects_for_workspace,
                workspace_id,
                opts,
            )
        return await self._run(self.projects.get_projects, opts)

    async def create_project(
        self,
        body: dict[str, Any],
        project_fields: str,
    ) -> dict[str, Any]:
        return await self._run(
            self.projects.create_project,
            body,
            self._opts_with_timeout(opt_fields=project_fields),
        )

    async def update_project(
        self,
        project_id: str,
        body: dict[str, Any],
        project_fields: str,
    ) -> dict[str, Any]:
        return await self._run(
            self.projects.update_project,
            body,
            project_id,
            self._opts_with_timeout(opt_fields=project_fields),
        )

    async def delete_project(self, project_id: str) -> None:
        await self._run(
            self.projects.delete_project,
            project_id,
            _request_timeout=self._config.timeout_seconds,
        )

