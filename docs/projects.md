# Projects

## Methods
```python
await client.list_workspaces() -> list[Workspace]
await client.get_project(project_id: str) -> Project
await client.list_projects(workspace_id: str | None = None) -> list[Project]
await client.create_project(payload: CreateProjectInput) -> Project
await client.update_project(project_id: str, payload: UpdateProjectInput) -> Project
await client.delete_project(project_id: str) -> None
```

## Models

### Workspace
- `id`: `str`
- `name`: `str`
- `key`: `str | None`

### Project
- `id`: `str`
- `name`: `str`
- `key`: `str | None`
- `description`: `str | None`
- `workspace_id`: `str | None`

### CreateProjectInput
- `name`: `str`
- `key`: `str | None`
- `description`: `str | None`
- `workspace_id`: `str | None`

### UpdateProjectInput
- `name`: `str | None`
- `key`: `str | None`
- `description`: `str | None`

## Notes
- `Workspace` is a top-level container above projects.
- `workspace_id` in `list_projects()` can be omitted.
- provider-specific limitations should raise `ProviderCapabilityError`.
- `Jira`, `Yandex Tracker`, and `Asana` implement this section of the contract.
- In `Yandex Tracker`, official documentation distinguishes `queue` and native `project` as separate entities.
- In `Yandex Tracker`, every issue belongs to a queue, while native `project` is a higher-level entity that can include queues.
- In `trackerkit`, shared `Project` is mapped to the provider entity that acts as the main operational task container.
- For `Yandex Tracker`, this means shared `Project` is mapped to `queue`.
- For `Yandex Tracker`, `Project.id` and `Project.key` are based on the queue key.
- For `Yandex Tracker`, `create_project()` creates a queue under the hood.
- For `Yandex Tracker`, `update_project()` and `delete_project()` update and delete the same queue.
- The public library API is async, while some provider transports may wrap sync SDKs internally.

## Canonical Mapping
The shared `Project` model represents the main operational container for tasks in each provider.
This is a canonical integration decision made on top of provider source models, not a claim that provider-native names are identical.

| Shared entity | Jira | Yandex Tracker | Asana |
| --- | --- | --- | --- |
| `Workspace` | integration-level container for one Jira site / instance | organization context | Asana workspace |
| `Project` | Jira project | queue | Asana project |

### Provider notes
- `Jira`: `Project` maps to Jira project.
- `Yandex Tracker`: `Project` maps to queue, not to the native Yandex Tracker `project` entity.
- `Asana`: `Project` maps to Asana project.

## Source Grounding
- Jira documentation describes a project/space as a configurable container for work items.
- Yandex Tracker documentation states that every issue belongs to a queue and separately documents native `project` with queues as an expandable field.
- Asana documentation describes a project as a prioritized list of tasks or a board inside a workspace or organization.

## Sources
- Jira: [Projects / spaces overview](https://www.atlassian.com/software/jira/guides/projects/overview)
- Yandex Tracker: [Queue introduction](https://yandex.ru/support/tracker/en/queue-intro)
- Yandex Tracker: [Get project parameters](https://yandex.ru/support/tracker/en/api-ref/projects/get-project)
- Asana: [Projects reference](https://developers.asana.com/reference/projects)

## Entity Relationship
- `Workspace` contains many `Project`.
- `Project` contains many `Task`.
- In `Yandex Tracker`, this means: organization/workspace -> queue -> issues.

## Example
```python
from trackerkit import (
    CreateProjectInput,
    TrackerClient,
    UpdateProjectInput,
)

client = TrackerClient(
    provider="jira",
    auth_data={
        "base_url": "https://your-domain.atlassian.net",
        "access_token": "secret",
    },
)

workspaces = await client.list_workspaces()
projects = await client.list_projects()

project = await client.create_project(
    CreateProjectInput(
        name="Platform",
        key="PLATFORM",
        description="Platform team project",
    )
)

updated = await client.update_project(
    project.id,
    UpdateProjectInput(description="Updated description"),
)

await client.delete_project(updated.id)
```
