"""Unit tests for `JiraQueryBuilder` — JQL escaping (CORR-1)."""

from datetime import datetime

from trackerkit.domain.models import TaskQuery
from trackerkit.providers.jira.queries import JiraQueryBuilder


def test_build_jql_with_no_query_returns_default_order() -> None:
    builder = JiraQueryBuilder()
    jql, fields = builder.build_task_search(None)
    assert jql == "order by updated DESC"
    assert "summary" in fields


def test_build_jql_with_empty_query_returns_default_order() -> None:
    builder = JiraQueryBuilder()
    jql, _ = builder.build_task_search(TaskQuery())
    assert jql == "order by updated DESC"


def test_build_jql_escapes_double_quotes_in_project_id() -> None:
    builder = JiraQueryBuilder()
    jql, _ = builder.build_task_search(TaskQuery(project_id='PRJ"INJECT'))
    assert 'project = "PRJ\\"INJECT"' in jql


def test_build_jql_escapes_backslash_in_assignee_id() -> None:
    builder = JiraQueryBuilder()
    jql, _ = builder.build_task_search(TaskQuery(assignee_id="back\\slash"))
    assert 'assignee = "back\\\\slash"' in jql


def test_build_jql_combines_clauses_with_and() -> None:
    builder = JiraQueryBuilder()
    jql, _ = builder.build_task_search(
        TaskQuery(project_id="ABC", status_id="To Do")
    )
    assert "project = \"ABC\"" in jql
    assert "status = \"To Do\"" in jql
    assert " AND " in jql
    assert jql.endswith("ORDER BY updated DESC")


def test_build_jql_includes_updated_since_clause() -> None:
    builder = JiraQueryBuilder()
    when = datetime(2025, 1, 2, 10, 30)
    jql, _ = builder.build_task_search(TaskQuery(updated_since=when))
    assert 'updated >= "2025-01-02 10:30"' in jql
