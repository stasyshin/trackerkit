from depensee_tracker_client.domain.models import Task, TaskQuery


class AsanaQueryPolicy:
    def task_fields(self) -> str:
        return ",".join(
            [
                "gid",
                "name",
                "notes",
                "projects.gid",
                "memberships.project.gid",
                "assignee.gid",
                "assignee.name",
                "assignee.email",
                "completed",
                "created_at",
                "modified_at",
                "due_at",
                "due_on",
                "permalink_url",
            ]
        )

    def project_fields(self) -> str:
        return "gid,name,notes,workspace.gid"

    def workspace_fields(self) -> str:
        return "gid,name"

    def filter_tasks(self, tasks: list[Task], query: TaskQuery | None) -> list[Task]:
        effective_query = query or TaskQuery()
        filtered = tasks

        if effective_query.assignee_id is not None:
            filtered = [
                task
                for task in filtered
                if task.assignee is not None and task.assignee.id == effective_query.assignee_id
            ]

        if effective_query.status_id is not None:
            expected = effective_query.status_id.lower()
            filtered = [
                task
                for task in filtered
                if task.status is not None and task.status.id.lower() == expected
            ]

        if effective_query.updated_since is not None:
            filtered = [
                task
                for task in filtered
                if task.updated_at is not None and task.updated_at >= effective_query.updated_since
            ]

        return filtered

