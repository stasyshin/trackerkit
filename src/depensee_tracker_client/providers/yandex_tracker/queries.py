from depensee_tracker_client.domain.models import Task, TaskQuery


class YandexTrackerQueryPolicy:
    def build_issue_search_params(self, query: TaskQuery | None) -> dict:
        effective_query = query or TaskQuery()
        return {
            "query": None,
            "queue": effective_query.project_id,
        }

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
            filtered = [
                task
                for task in filtered
                if task.status is not None and task.status.id == effective_query.status_id
            ]

        if effective_query.updated_since is not None:
            filtered = [
                task
                for task in filtered
                if task.updated_at is not None and task.updated_at >= effective_query.updated_since
            ]

        return filtered

