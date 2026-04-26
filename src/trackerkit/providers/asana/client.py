from typing import Any

from trackerkit.contracts.auth import AsanaAuthConfig
from trackerkit.domain.errors import ProviderCapabilityError
from trackerkit.domain.models import (
    ConnectionDiagnostic,
    CreateProjectInput,
    CreateTaskInput,
    Project,
    Task,
    TaskQuery,
    UpdateProjectInput,
    UpdateTaskInput,
    Workspace,
)
from trackerkit.domain.relation_mapping import RelationMappingConfig
from trackerkit.providers.asana.mappers import AsanaMapper
from trackerkit.providers.asana.queries import AsanaQueryPolicy
from trackerkit.providers.asana.transport import AsanaTransport
from trackerkit.providers.base import BaseTaskTrackerAdapter


class AsanaClient(BaseTaskTrackerAdapter):
    provider_name = "Asana"

    def __init__(
        self,
        config: AsanaAuthConfig,
        relation_mapping: RelationMappingConfig | None = None,
    ) -> None:
        # `relation_mapping` is intentionally accepted but not used yet.
        # Asana relation CRUD is unimplemented, so `BaseTaskTrackerAdapter`
        # raises `ProviderCapabilityError` on relation operations.
        self._relation_mapping = relation_mapping
        self._transport = AsanaTransport(config)
        self._mapper = AsanaMapper()
        self._queries = AsanaQueryPolicy()

    # Default page cap when callers do not pass `TaskQuery.limit`. Avoids
    # eagerly draining a paginated SDK response for large workspaces.
    _DEFAULT_TASK_LIMIT = 200

    def _materialize(self, value: Any, limit: int | None = None) -> list[dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, list):
            return value if limit is None else value[:limit]
        result: list[dict[str, Any]] = []
        for item in value:
            if limit is not None and len(result) >= limit:
                break
            result.append(item)
        return result

    async def check_connection(self) -> bool:
        return await self._transport.check_connection(self._queries.workspace_fields())

    async def get_connection_diagnostic(self) -> ConnectionDiagnostic:
        return await self._transport.get_connection_diagnostic(
            self._queries.workspace_fields()
        )

    async def get_task(self, task_id: str) -> Task:
        task = await self._transport.get_task(task_id, self._queries.task_fields())
        return self._mapper.to_task(task)

    async def list_tasks(self, query: TaskQuery | None = None) -> list[Task]:
        effective_query = query or TaskQuery()
        if effective_query.project_id is None:
            raise ProviderCapabilityError(
                "Asana list_tasks requires a TaskQuery.project_id. Walking every "
                "workspace and project would issue an unbounded number of API calls."
            )
        limit = effective_query.limit or self._DEFAULT_TASK_LIMIT
        result = await self._transport.get_tasks_for_project(
            effective_query.project_id,
            self._queries.task_fields(),
        )
        raw_tasks = self._materialize(result, limit=limit)
        tasks = [self._mapper.to_task(item) for item in raw_tasks]
        return self._queries.filter_tasks(tasks, query)

    async def create_task(self, payload: CreateTaskInput) -> Task:
        body: dict[str, Any] = {"data": {"name": payload.title}}
        if payload.description is not None:
            body["data"]["notes"] = payload.description
        if payload.project_id is not None:
            body["data"]["projects"] = [payload.project_id]
        if payload.assignee_id is not None:
            body["data"]["assignee"] = payload.assignee_id
        if payload.due_date is not None:
            body["data"]["due_at"] = payload.due_date.isoformat()
        task = await self._transport.create_task(body, self._queries.task_fields())
        if payload.status_id is not None:
            return await self.update_task(
                str(task["gid"]),
                UpdateTaskInput(status_id=payload.status_id),
            )
        return self._mapper.to_task(task)

    async def update_task(self, task_id: str, payload: UpdateTaskInput) -> Task:
        body: dict[str, Any] = {"data": {}}
        if payload.title is not None:
            body["data"]["name"] = payload.title
        if payload.description is not None:
            body["data"]["notes"] = payload.description
        if payload.assignee_id is not None:
            body["data"]["assignee"] = payload.assignee_id
        if payload.due_date is not None:
            body["data"]["due_at"] = payload.due_date.isoformat()
        if payload.status_id is not None:
            normalized = payload.status_id.lower()
            body["data"]["completed"] = normalized in {"done", "completed", "complete"}
        task = await self._transport.update_task(
            task_id,
            body,
            self._queries.task_fields(),
        )
        return self._mapper.to_task(task)

    async def delete_task(self, task_id: str) -> None:
        await self._transport.delete_task(task_id)

    async def list_workspaces(self) -> list[Workspace]:
        workspaces = await self._transport.get_workspaces(self._queries.workspace_fields())
        return [
            self._mapper.to_workspace(item)
            for item in self._materialize(workspaces, limit=self._DEFAULT_TASK_LIMIT)
        ]

    async def get_project(self, project_id: str) -> Project:
        project = await self._transport.get_project(project_id, self._queries.project_fields())
        return self._mapper.to_project(project)

    async def list_projects(self, workspace_id: str | None = None) -> list[Project]:
        projects = await self._transport.get_projects(
            workspace_id,
            self._queries.project_fields(),
        )
        return [
            self._mapper.to_project(item)
            for item in self._materialize(projects, limit=self._DEFAULT_TASK_LIMIT)
        ]

    async def create_project(self, payload: CreateProjectInput) -> Project:
        if payload.key is not None:
            raise ProviderCapabilityError(
                "Asana projects do not support a shared key field in this adapter."
            )
        if payload.workspace_id is None:
            raise ProviderCapabilityError("Asana project creation requires workspace_id.")
        body = {
            "data": {
                "name": payload.name,
                "workspace": payload.workspace_id,
            }
        }
        if payload.description is not None:
            body["data"]["notes"] = payload.description
        project = await self._transport.create_project(
            body,
            self._queries.project_fields(),
        )
        return self._mapper.to_project(project)

    async def update_project(
        self,
        project_id: str,
        payload: UpdateProjectInput,
    ) -> Project:
        if payload.key is not None:
            raise ProviderCapabilityError(
                "Asana projects do not support a shared key field in this adapter."
            )
        body: dict[str, Any] = {"data": {}}
        if payload.name is not None:
            body["data"]["name"] = payload.name
        if payload.description is not None:
            body["data"]["notes"] = payload.description
        project = await self._transport.update_project(
            project_id,
            body,
            self._queries.project_fields(),
        )
        return self._mapper.to_project(project)

    async def delete_project(self, project_id: str) -> None:
        await self._transport.delete_project(project_id)

