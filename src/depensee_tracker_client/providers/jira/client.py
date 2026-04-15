from typing import Any

from depensee_tracker_client.contracts.auth import JiraAuthConfig
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
from depensee_tracker_client.providers.base import BaseTaskTrackerAdapter
from depensee_tracker_client.providers.jira.mappers import JiraMapper
from depensee_tracker_client.providers.jira.queries import JiraQueryBuilder
from depensee_tracker_client.providers.jira.transport import JiraTransport


class JiraClient(BaseTaskTrackerAdapter):
    provider_name = "Jira"

    def __init__(self, config: JiraAuthConfig) -> None:
        self._transport = JiraTransport(config)
        self._mapper = JiraMapper(config.base_url)
        self._queries = JiraQueryBuilder()

    async def check_connection(self) -> bool:
        return await self._transport.check_connection()

    async def get_connection_diagnostic(self) -> ConnectionDiagnostic:
        return await self._transport.get_connection_diagnostic()

    async def get_task(self, task_id: str) -> Task:
        issue = await self._transport.get_issue(task_id, self._queries.task_fields)
        return self._mapper.to_task(issue)

    async def list_tasks(self, query: TaskQuery | None = None) -> list[Task]:
        jql, fields = self._queries.build_task_search(query)
        issues = await self._transport.search_issues(jql, fields)
        return [self._mapper.to_task(issue) for issue in issues]

    async def create_task(self, payload: CreateTaskInput) -> Task:
        if payload.project_id is None:
            raise ProviderCapabilityError("Jira task creation requires project_id.")
        fields: dict[str, Any] = {
            "project": payload.project_id,
            "issuetype": {"name": "Task"},
            "summary": payload.title,
        }
        if payload.description is not None:
            fields["description"] = payload.description
        if payload.assignee_id is not None:
            fields["assignee"] = {"accountId": payload.assignee_id}
        if payload.due_date is not None:
            fields["duedate"] = payload.due_date.date().isoformat()
        issue = await self._transport.create_issue(fields)
        if payload.status_id is not None:
            await self._transport.transition_issue(issue, payload.status_id)
        refreshed = await self._transport.get_issue(issue.key, self._queries.task_fields)
        return self._mapper.to_task(refreshed)

    async def update_task(self, task_id: str, payload: UpdateTaskInput) -> Task:
        issue = await self._transport.get_issue(task_id, self._queries.task_fields)
        fields: dict[str, Any] = {}
        if payload.title is not None:
            fields["summary"] = payload.title
        if payload.description is not None:
            fields["description"] = payload.description
        if payload.assignee_id is not None:
            fields["assignee"] = {"accountId": payload.assignee_id}
        if payload.due_date is not None:
            fields["duedate"] = payload.due_date.date().isoformat()
        if fields:
            await self._transport.update_issue_fields(issue, fields)
        if payload.status_id is not None:
            await self._transport.transition_issue(issue, payload.status_id)
        refreshed = await self._transport.get_issue(task_id, self._queries.task_fields)
        return self._mapper.to_task(refreshed)

    async def delete_task(self, task_id: str) -> None:
        issue = await self._transport.get_issue(task_id, self._queries.task_fields)
        await self._transport.delete_issue(issue)

    async def list_workspaces(self) -> list[Workspace]:
        return [self._mapper.to_workspace()]

    async def get_project(self, project_id: str) -> Project:
        project = await self._transport.get_project(project_id)
        return self._mapper.to_project(project)

    async def list_projects(self, workspace_id: str | None = None) -> list[Project]:
        if workspace_id is not None and workspace_id != self._mapper.to_workspace().id:
            return []
        projects = await self._transport.get_projects()
        return [self._mapper.to_project(project) for project in projects]

    async def create_project(self, payload: CreateProjectInput) -> Project:
        if payload.key is None:
            raise ProviderCapabilityError("Jira project creation requires key.")
        project_id = await self._transport.create_project(
            key=payload.key,
            name=payload.name,
        )
        project = await self._transport.get_project(str(project_id))
        if payload.description is not None:
            return await self.update_project(
                str(project.id),
                UpdateProjectInput(description=payload.description),
            )
        return self._mapper.to_project(project)

    async def update_project(
        self,
        project_id: str,
        payload: UpdateProjectInput,
    ) -> Project:
        data: dict[str, Any] = {}
        if payload.name is not None:
            data["name"] = payload.name
        if payload.key is not None:
            data["key"] = payload.key
        if payload.description is not None:
            data["description"] = payload.description
        if data:
            await self._transport.update_project(project_id, data)
        return await self.get_project(project_id)

    async def delete_project(self, project_id: str) -> None:
        await self._transport.delete_project(project_id)

