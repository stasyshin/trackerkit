from typing import Any

from depensee_tracker_client.contracts.auth import AsanaAuthConfig
from depensee_tracker_client.domain.errors import ProviderCapabilityError
from depensee_tracker_client.domain.models import (
    Comment,
    ConnectionDiagnostic,
    CreateCommentInput,
    CreateProjectInput,
    CreateRelationInput,
    CreateTaskInput,
    Project,
    Relation,
    Status,
    Task,
    TaskQuery,
    UpdateProjectInput,
    UpdateTaskInput,
    User,
    Workspace,
)
from depensee_tracker_client.domain.relation_mapping import RelationMappingConfig
from depensee_tracker_client.providers.asana.mappers import AsanaMapper
from depensee_tracker_client.providers.asana.queries import AsanaQueryPolicy
from depensee_tracker_client.providers.asana.transport import AsanaTransport
from depensee_tracker_client.providers.base import BaseTaskTrackerAdapter


class AsanaClient(BaseTaskTrackerAdapter):
    provider_name = "Asana"

    def __init__(
        self,
        config: AsanaAuthConfig,
        relation_mapping: RelationMappingConfig | None = None,
    ) -> None:
        del relation_mapping
        self._transport = AsanaTransport(config)
        self._mapper = AsanaMapper()
        self._queries = AsanaQueryPolicy()

    def _materialize(self, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return list(value)

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
        raw_tasks: list[dict[str, Any]] = []
        if effective_query.project_id is not None:
            result = await self._transport.get_tasks_for_project(
                effective_query.project_id,
                self._queries.task_fields(),
            )
            raw_tasks = self._materialize(result)
        else:
            seen_ids: set[str] = set()
            workspaces = await self.list_workspaces()
            for workspace in workspaces:
                projects = await self.list_projects(workspace.id)
                for project in projects:
                    result = await self._transport.get_tasks_for_project(
                        project.id,
                        self._queries.task_fields(),
                    )
                    for item in self._materialize(result):
                        if item["gid"] in seen_ids:
                            continue
                        seen_ids.add(item["gid"])
                        raw_tasks.append(item)
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
        return [self._mapper.to_workspace(item) for item in self._materialize(workspaces)]

    async def get_project(self, project_id: str) -> Project:
        project = await self._transport.get_project(project_id, self._queries.project_fields())
        return self._mapper.to_project(project)

    async def list_projects(self, workspace_id: str | None = None) -> list[Project]:
        projects = await self._transport.get_projects(
            workspace_id,
            self._queries.project_fields(),
        )
        return [self._mapper.to_project(item) for item in self._materialize(projects)]

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

