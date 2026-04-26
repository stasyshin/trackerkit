# Tasks

## Methods
```python
await client.get_task(task_id: str) -> Task
await client.list_tasks(query: TaskQuery | None = None) -> list[Task]
await client.create_task(payload: CreateTaskInput) -> Task
await client.update_task(task_id: str, payload: UpdateTaskInput) -> Task
await client.delete_task(task_id: str) -> None
```

## Models

### Task
- `id`: `str`
- `key`: `str | None`
- `title`: `str`
- `description`: `str | None`
- `project_id`: `str | None`
- `status`: `Status | None`
- `assignee`: `User | None`
- `reporter`: `User | None`
- `created_at`: `datetime | None`
- `updated_at`: `datetime | None`
- `due_date`: `datetime | None`
- `url`: `str | None`

### TaskQuery
- `project_id`: `str | None`
- `assignee_id`: `str | None`
- `status_id`: `str | None`
- `updated_since`: `datetime | None`

### CreateTaskInput
- `title`: `str`
- `description`: `str | None`
- `project_id`: `str | None`
- `assignee_id`: `str | None`
- `status_id`: `str | None`
- `due_date`: `datetime | None`

### UpdateTaskInput
- `title`: `str | None`
- `description`: `str | None`
- `assignee_id`: `str | None`
- `status_id`: `str | None`
- `due_date`: `datetime | None`

## Notes
- `get_task()` returns one task by provider-specific identifier.
- `list_tasks()` supports a common query model only.
- provider-specific fields are intentionally excluded from the shared contract.
- `Jira`, `Yandex Tracker`, and `Asana` implement this section of the contract.
- In `Yandex Tracker`, unified `Task` maps to issue.
- In `Yandex Tracker`, `Task.project_id` maps to queue key.
- In `Yandex Tracker`, `create_task()` sends `project_id` as the target queue.
- In `Yandex Tracker`, direct issue deletion is not supported in the same way as in some other providers, so `delete_task()` should be treated as unsupported capability unless a provider-specific close/archive workflow is introduced.
- Some status transitions still depend on provider-specific rules and permissions.
- The public library API is async, while some provider transports may wrap sync SDKs internally.

## Provider Mapping
- `Jira`: `Task` maps to issue.
- `Yandex Tracker`: `Task` maps to issue inside queue.
- `Asana`: `Task` maps to task.

## Entity Relationship
- `Task.project_id` points to the parent `Project`.
- In `Yandex Tracker`, this means each task belongs to a queue represented by unified `Project`.

## Relation Mapping
`Relation` is a shared task-to-task edge in the canonical model.
The detailed CRUD contract and provider-specific mapping rules live in `docs/relations.md`.

| Shared entity | Jira | Yandex Tracker | Asana |
| --- | --- | --- | --- |
| `Relation` | issue link with configurable inward / outward type labels | issue link with explicit relationship value and direction | dependency / dependent edge between tasks |

### Source-grounded notes
- Jira issue links are bidirectional and depend on configured link types such as `Blocks` with inward / outward labels.
- Yandex Tracker links are created with explicit relationship values such as `relates`, `depends on`, `is dependent by`, plus hierarchy-oriented variants.
- Asana exposes dependencies and dependents for tasks, so it naturally covers blocking order but not a broad relation taxonomy like Jira or Yandex Tracker.
- Because of that mismatch, a shared `RelationType` should stay limited to the intersection that can be normalized safely across providers.

## Product-first Core Relation Semantics
For the product concept, the primary relation set should be optimized for visual planning rather than for exhaustive provider parity.

The core set is:
- `relates` - weak semantic connection;
- `blocks` - directed blocking or unlock dependency;
- `contains` - structural inclusion, decomposition, or parent-child relation.

| Core relation | Product meaning | Default visual style | Jira | Yandex Tracker | Asana |
| --- | --- | --- | --- | --- | --- |
| `relates` | weak semantic connection without strict dependency | dashed line | symmetric relates-style issue link when configured | native `relates` | no direct native equivalent |
| `blocks` | one task blocks or unlocks another | directed arrow | Blocks-style issue link direction | `depends on` / `is dependent by` | dependencies / dependents |
| `contains` | one task includes or structurally owns another | solid line | parent-child or subtask hierarchy | `is parent task for` / `is subtask for`, plus epic-style hierarchy when relevant | subtasks |

### Non-core provider relations
- Provider-specific relation variants such as duplicates, clones, epics, or custom hierarchy levels are not part of the public `RelationType` enum.
- If imported later, they should be treated as provider metadata or normalized into one of the three core relation types only when that preserves the product meaning.

### Modeling note
- This product-facing taxonomy is a better fit for the canvas concept than a provider-driven list of all possible external link types.
- Provider adapters may ingest richer native link types and normalize only the planning-relevant subset into the shared visual model.

## Sources
- Jira: [Issue linking model](https://developer.atlassian.com/cloud/jira/platform/issue-linking-model/)
- Jira: [Configure the work type hierarchy](https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/)
- Yandex Tracker: [Linking issues](https://yandex.ru/support/tracker/en/api-ref/issues/link-issue)
- Asana: [Tasks reference](https://developers.asana.com/reference/tasks)
- Asana: [Set dependencies for a task](https://developers.asana.com/reference/adddependenciesfortask)
- Asana: [Get dependents from a task](https://developers.asana.com/reference/getdependentsfortask)
- Asana: [Object hierarchy](https://developers.asana.com/docs/object-hierarchy)

## Example
```python
from trackerkit import (
    CreateTaskInput,
    TaskQuery,
    TrackerClient,
    UpdateTaskInput,
)

client = TrackerClient(
    provider="jira",
    auth_data={
        "base_url": "https://your-domain.atlassian.net",
        "access_token": "secret",
    },
)

tasks = await client.list_tasks(TaskQuery(project_id="10000"))

created = await client.create_task(
    CreateTaskInput(
        title="Prepare release notes",
        description="Draft the release notes for sprint 12",
        project_id="10000",
    )
)

task = await client.get_task(created.id)

updated = await client.update_task(
    created.id,
    UpdateTaskInput(description="Updated release notes draft"),
)

await client.delete_task(updated.id)
```
