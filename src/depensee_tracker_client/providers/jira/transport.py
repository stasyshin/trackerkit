import asyncio
import json
from typing import Any

from jira import JIRA
from jira.exceptions import JIRAError

from depensee_tracker_client.contracts.auth import JiraAuthConfig
from depensee_tracker_client.domain.enums import Provider
from depensee_tracker_client.domain.errors import get_error_kind
from depensee_tracker_client.domain.models import ConnectionDiagnostic
from depensee_tracker_client.providers.jira.errors import raise_jira_error, raise_jira_project_creation_error


class JiraTransport:
    def __init__(self, config: JiraAuthConfig) -> None:
        self._config = config
        self._client: JIRA | None = None
        self._last_issue_link_debug: dict[str, Any] | None = None

    def _get_client(self) -> JIRA:
        if self._client is None:
            options = {"server": self._config.base_url.rstrip("/")}
            token = self._config.access_token or self._config.api_token or ""
            self._client = JIRA(
                options=options,
                token_auth=token,
                validate=False,
                get_server_info=False,
                max_retries=self._config.max_retries,
                timeout=self._config.timeout_seconds,
            )
        return self._client

    async def _run(self, func, /, *args, **kwargs):
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except JIRAError as error:
            raise_jira_error(error)

    async def check_connection(self) -> bool:
        diagnostic = await self.get_connection_diagnostic()
        return diagnostic.is_connected

    async def get_connection_diagnostic(self) -> ConnectionDiagnostic:
        try:
            await self._run(self._get_client().myself)
        except Exception as error:
            return ConnectionDiagnostic(
                provider=Provider.JIRA,
                is_connected=False,
                error_kind=get_error_kind(error),
                message=str(error),
                error_type=type(error).__name__,
            )
        return ConnectionDiagnostic(
            provider=Provider.JIRA,
            is_connected=True,
        )

    async def get_issue(self, task_id: str, fields: str) -> Any:
        return await self._run(self._get_client().issue, task_id, fields=fields)

    async def search_issues(
        self,
        jql: str,
        fields: str,
    ) -> list[Any]:
        return await self._run(
            self._get_client().search_issues,
            jql,
            0,
            False,
            True,
            fields,
        )

    async def create_issue(self, fields: dict[str, Any]) -> Any:
        return await self._run(self._get_client().create_issue, fields=fields)

    async def update_issue_fields(self, issue: Any, fields: dict[str, Any]) -> None:
        await self._run(issue.update, fields=fields)

    async def set_issue_parent(self, task_id: str, parent_task_id: str) -> None:
        issue = await self.get_issue(task_id, "parent")
        await self.update_issue_fields(issue, {"parent": {"id": parent_task_id}})

    async def get_issue_key(self, task_id: str) -> str:
        issue = await self.get_issue(task_id, "key")
        return str(issue.key)

    async def transition_issue(self, issue: Any, transition: str) -> None:
        await self._run(self._get_client().transition_issue, issue, transition)

    async def delete_issue(self, issue: Any) -> None:
        await self._run(issue.delete)

    async def get_issue_link(self, relation_id: str) -> Any:
        return await self._run(self._get_client().issue_link, relation_id)

    def get_last_issue_link_debug(self) -> dict[str, Any] | None:
        return self._last_issue_link_debug

    async def create_issue_link(
        self,
        link_type_name: str,
        source_task_id: str,
        target_task_id: str,
    ) -> str | None:
        source_issue_key = await self.get_issue_key(source_task_id)
        target_issue_key = await self.get_issue_key(target_task_id)
        response = await self._run(
            self._get_client().create_issue_link,
            link_type_name,
            target_issue_key,
            source_issue_key,
        )
        status_code = getattr(response, "status_code", None)
        response_text = getattr(response, "text", None)
        try:
            payload = response.json()
        except ValueError:
            payload = None
        self._last_issue_link_debug = {
            "link_type_name": link_type_name,
            "source_task_id": source_task_id,
            "target_task_id": target_task_id,
            "source_issue_key": source_issue_key,
            "target_issue_key": target_issue_key,
            "status_code": status_code,
            "response_text": response_text,
            "response_json": payload,
        }
        if payload is None:
            return None
        relation_id = payload.get("id")
        return str(relation_id) if relation_id is not None else None

    async def delete_issue_link(self, relation_id: str) -> None:
        await self._run(self._get_client().delete_issue_link, relation_id)

    async def get_projects(self) -> list[Any]:
        return await self._run(self._get_client().projects)

    async def get_project(self, project_id: str) -> Any:
        return await self._run(self._get_client().project, project_id)

    async def create_project(self, key: str, name: str) -> str:
        try:
            return await self._run(self._get_client().create_project, key=key, name=name)
        except RuntimeError as error:
            raise_jira_project_creation_error(error)

    async def update_project(self, project_id: str, data: dict[str, Any]) -> None:
        client = self._get_client()
        url = client._get_url(f"project/{project_id}")
        await self._run(client._session.put, url, data=json.dumps(data))

    async def delete_project(self, project_id: str) -> None:
        await self._run(self._get_client().delete_project, project_id)

