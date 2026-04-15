from datetime import UTC, datetime
from typing import Any

from depensee_tracker_client.domain.models import Project, Status, Task, User, Workspace


class AsanaMapper:
    def to_workspace(self, value: dict[str, Any]) -> Workspace:
        return Workspace(
            id=str(value["gid"]),
            name=str(value.get("name") or value["gid"]),
            key=None,
        )

    def to_project(self, value: dict[str, Any]) -> Project:
        workspace = value.get("workspace") or {}
        return Project(
            id=str(value["gid"]),
            name=str(value.get("name") or value["gid"]),
            key=None,
            description=value.get("notes"),
            workspace_id=workspace.get("gid"),
        )

    def to_task(self, value: dict[str, Any]) -> Task:
        projects = value.get("projects") or []
        memberships = value.get("memberships") or []
        project_id = None
        if projects:
            project_id = projects[0].get("gid")
        elif memberships and memberships[0].get("project"):
            project_id = memberships[0]["project"].get("gid")

        return Task(
            id=str(value["gid"]),
            key=None,
            title=str(value.get("name") or value["gid"]),
            description=value.get("notes"),
            project_id=project_id,
            status=self._to_status(value),
            assignee=self._to_user(value.get("assignee")),
            reporter=None,
            created_at=self._parse_datetime(value.get("created_at")),
            updated_at=self._parse_datetime(value.get("modified_at")),
            due_date=self._parse_datetime(value.get("due_at") or value.get("due_on")),
            url=value.get("permalink_url"),
        )

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            try:
                parsed = datetime.fromisoformat(f"{normalized}T00:00:00")
            except ValueError:
                return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    def _to_user(self, value: dict[str, Any] | None) -> User | None:
        if not value:
            return None
        return User(
            id=str(value["gid"]),
            display_name=str(value.get("name") or value["gid"]),
            email=value.get("email"),
        )

    def _to_status(self, task: dict[str, Any]) -> Status:
        completed = bool(task.get("completed"))
        return Status(
            id="completed" if completed else "incomplete",
            name="Completed" if completed else "Incomplete",
            category="done" if completed else "todo",
        )

