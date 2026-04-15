from depensee_tracker_client.domain.models import TaskQuery


class JiraQueryBuilder:
    task_fields = (
        "summary,description,project,status,assignee,reporter,created,updated,duedate"
    )

    def build_task_search(self, query: TaskQuery | None) -> tuple[str, str]:
        return (self._build_jql(query), self.task_fields)

    def _build_jql(self, query: TaskQuery | None) -> str:
        if query is None:
            return "order by updated DESC"

        clauses: list[str] = []

        if query.project_id:
            clauses.append(f'project = "{query.project_id}"')
        if query.assignee_id:
            clauses.append(f'assignee = "{query.assignee_id}"')
        if query.status_id:
            clauses.append(f'status = "{query.status_id}"')
        if query.updated_since:
            clauses.append(
                f'updated >= "{query.updated_since.strftime("%Y-%m-%d %H:%M")}"'
            )

        if not clauses:
            return "order by updated DESC"

        return " AND ".join(clauses) + " ORDER BY updated DESC"

