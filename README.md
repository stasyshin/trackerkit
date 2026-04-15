# depensee-tracker-client

Unified async client library for Jira, Yandex Tracker, and Asana integrations.

## Status
- early-stage internal library;
- API and provider coverage may still evolve;
- currently focused on a shared contract for Jira, Yandex Tracker, and Asana.

## Installation

Install from a Git tag:

```bash
pip install "git+https://github.com/stasyshin/depensee-tracker-client.git@v0.1.0"
```

Install from the `main` branch:

```bash
pip install "git+https://github.com/stasyshin/depensee-tracker-client.git@main"
```

## Local development

```bash
poetry install
```

Install from the current project directory:

```bash
pip install .
```

## Goals
- provide one common contract for supported task trackers;
- hide provider-specific SDK details from the main backend;
- expose only shared entities and operations;
- keep the design extensible and testable.

## Supported providers
- Jira
- Yandex Tracker
- Asana

## Current scope
- one facade client per one selected task tracker;
- common async client contract;
- shared models for tasks, projects, users, comments, relations, and statuses;
- provider auth configs;
- real provider adapters for `workspaces`, `projects`, and `tasks`;
- client factory.

## Internal architecture
- capability-based contracts instead of one monolithic provider interface;
- `TrackerClient` facade with centralized connection guard;
- provider adapters split into `transport`, `queries`, `mappers`, and `errors`;
- domain models and auth configs remain typed with `Pydantic`;
- the public API stays async even when a provider transport uses a sync SDK under the hood.

## Package layout
```text
docs/
examples/
src/
└── depensee_tracker_client/
    ├── contracts/
    ├── domain/
    ├── factory/
    ├── providers/
    ├── tracker_client.py
    └── __init__.py
```

## Usage
```python
from depensee_tracker_client import TrackerClient

client = TrackerClient(
    provider="jira",
    auth_data={
        "base_url": "https://your-domain.atlassian.net",
        "access_token": "secret",
    },
    connection_timeout=3,
    max_retries=0,
)
```

## Development
- Python `3.12`
- package manager: `poetry`
- import root: `src`

### Local checks
Build the package locally:

```bash
python -m pip wheel . --no-deps
```

## Service integration
This library is designed to be embedded into a backend service.

- the library does not read environment variables by itself;
- the service loads configuration and passes typed `auth_data` into `TrackerClient`;
- connection behavior is configured via explicit `TrackerClient` arguments instead of `auth_data`;
- only `examples/` load local env files for manual development checks.

### Pydantic settings example
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

from depensee_tracker_client import TrackerClient


class JiraSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    base_url: str
    token: str


settings = JiraSettings()

client = TrackerClient(
    provider="jira",
    auth_data={
        "base_url": settings.base_url,
        "access_token": settings.token,
    },
    connection_timeout=3,
    max_retries=0,
)
```

## Documentation
- `docs/auth.md` - authorization and client initialization.
- `docs/projects.md` - workspaces and project methods.
- `docs/tasks.md` - task methods and task models.

## Examples
- `examples/jira_example.py` - Jira auth, projects flow, and task flow.
- `examples/yandex_example.py` - Yandex Tracker auth, projects flow, and task flow.
- `examples/asana_example.py` - Asana auth and readonly inspection flow.

## Notes
`src` is configured as the import root for the repository.

`Jira`, `Yandex Tracker`, and `Asana` already implement the shared `workspaces`, `projects`, and `tasks` contract. `users`, `comments`, and `relations` remain incremental follow-up work.

## Entity Mapping
`depensee-tracker-client` exposes a canonical task-tracker model.
This model is grounded in provider documentation first, then normalized into a shared contract for the backend.
Shared entities do not have to match provider-native names one to one.
They are mapped by functional role in the workflow, and some shared entities are integration-level abstractions rather than native provider objects.

### Provider source model
| Shared entity | Jira source model | Yandex Tracker source model | Asana source model |
| --- | --- | --- | --- |
| `Workspace` | integration-level container for one Jira site / instance | organization context selected by `X-Org-ID` or `X-Cloud-Org-ID` | native Asana workspace |
| `Project` | native Jira project | queue for operational task work; Yandex also has a separate native `project` entity above queues | native Asana project |
| `Task` | native Jira issue / work item | native Yandex issue in a queue | native Asana task |
| `Status` | native issue status | native issue status in queue workflow | task completion state and related task state fields |
| `User` | native Jira user | native Tracker user | native Asana user |
| `Relation` (planned) | native Jira issue link with configurable inward / outward link types | native issue link with explicit relationship type and direction | task dependency / dependent edge rather than a general-purpose typed link |

### Canonical mapping decision in `depensee-tracker-client`
- `Jira`: shared `Project` maps to Jira project, and shared `Task` maps to issue.
- `Yandex Tracker`: shared `Project` maps to queue, and shared `Task` maps to issue inside that queue.
- `Yandex Tracker`: native Yandex `project` is documented as a separate higher-level entity and is not part of the current shared contract.
- `Yandex Tracker`: direct issue deletion is not supported by the provider in the same way as in some other trackers, so task deletion should be modeled as unsupported or as a separate close/archive workflow.
- `Asana`: shared `Project` maps to Asana project, and shared `Task` maps to task.
- `Relation` is planned rather than fully implemented in the current public contract.
- `Jira`: planned shared `Relation` maps to issue links, but only the subset of link semantics that fits the shared enum should be normalized.
- `Yandex Tracker`: planned shared `Relation` maps to issue links; provider-native link types cover both dependency-style and hierarchy-style relations.
- `Asana`: planned shared `Relation` maps to task dependencies / dependents, so only dependency-style relations have a direct source-model equivalent.

### Product-first core relation semantics
For the product concept, the most important relation taxonomy is the one that supports canvas visualization and planning semantics.
The core visual set is smaller than the full set of provider-native link types.

| Core relation | Meaning in the product | Default visual style | Jira source model | Yandex Tracker source model | Asana source model |
| --- | --- | --- | --- | --- | --- |
| `relates` | weak semantic connection without strict dependency | dashed line | symmetric relates-style issue link when configured | native `relates` | no direct native equivalent |
| `blocks` | one task blocks or unlocks another | directed arrow | Blocks-style issue link direction | `depends on` / `is dependent by` | dependencies / dependents |
| `contains` | one task structurally includes, decomposes, or parents another | solid line | work item hierarchy such as parent-child or subtask hierarchy | `is parent task for` / `is subtask for`, plus epic-style hierarchy when relevant | subtasks |

### Secondary imported relations
- `duplicates` is not a core visual relation for the product and should be treated as secondary imported metadata rather than a primary canvas semantic.
- Provider-specific hierarchy variants such as epics or custom hierarchy levels can later be folded into `contains` when that preserves the planning meaning.

### Integration note
- The current domain enum is still a draft provider-oriented shape.
- The product-facing taxonomy above is the recommended direction for the next iteration of relation modeling.
- Jira allows custom issue link types, so label-based normalization must stay explicit and source-aware.
- Asana covers dependency and subtask hierarchy well, but does not provide a general-purpose typed link system equivalent to Jira or Yandex Tracker.

### Source notes
- Jira describes a project/space as a configurable container for work items.
- Yandex Tracker documents that every issue belongs to a queue, and also documents a separate native `project` entity that can include queues.
- Asana documents a project as a prioritized list of tasks or a board, and a task as the main work item inside workspaces and projects.
- Jira documents issue links as bidirectional links with configurable link types, each having inward and outward descriptions.
- Yandex Tracker documents links between issues with explicit relationship values such as `relates`, `depends on`, `is dependent by`, `duplicates`, and hierarchy-specific variants.
- Asana documents task dependencies and dependents, which model blocking order rather than a general relation taxonomy.
- Jira and Asana also document hierarchy-style task structures such as work item hierarchy and subtasks.
- Yandex Tracker documents hierarchy-oriented issue links such as parent-task and subtask relations.

### Sources
- Jira: [Projects / spaces overview](https://www.atlassian.com/software/jira/guides/projects/overview)
- Jira: [Issue linking model](https://developer.atlassian.com/cloud/jira/platform/issue-linking-model/)
- Yandex Tracker: [Queue introduction](https://yandex.ru/support/tracker/en/queue-intro)
- Yandex Tracker: [Get project parameters](https://yandex.ru/support/tracker/en/api-ref/projects/get-project)
- Yandex Tracker: [Linking issues](https://yandex.ru/support/tracker/en/api-ref/issues/link-issue)
- Asana: [Projects reference](https://developers.asana.com/reference/projects)
- Asana: [Tasks reference](https://developers.asana.com/reference/tasks)
- Asana: [Set dependencies for a task](https://developers.asana.com/reference/adddependenciesfortask)
- Asana: [Get dependents from a task](https://developers.asana.com/reference/getdependentsfortask)

Examples use environment variables instead of hardcoded credentials:
- `JIRA_BASE_URL`
- `JIRA_TOKEN`
- `YANDEX_TOKEN`
- `YANDEX_CLOUD_ORG_ID` - use one of `YANDEX_CLOUD_ORG_ID` or `YANDEX_ORG_ID`
- `YANDEX_ORG_ID` - use one of `YANDEX_CLOUD_ORG_ID` or `YANDEX_ORG_ID`
- `ASANA_TOKEN`
- `ASANA_PROJECT_ID` - optional, enables Asana task listing

Local development files:
- `.env.example` - fallback template for local example runs
- `.env` - local override for real local credentials

Examples load variables with this priority:
1. process environment
2. `.env`
3. `.env.example`

## Next steps
- validate `Yandex Tracker` adapter on real example flows the same way as Jira examples;
- add and verify examples for `Yandex Tracker` CRUD scenarios;
- start designing and implementing shared support for task relations;
- extend docs once relations move from planned scope into the public contract.
