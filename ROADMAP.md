# Roadmap

`trackerkit` is a unified async client for task trackers.
The main product goal is to expose one stable task/project/relation contract
while hiding provider SDK details from the host backend.

## Current status

### Done
- Public async `TrackerClient` facade for one selected provider.
- Typed auth configs for Jira, Yandex Tracker, and Asana.
- Shared domain models for workspaces, projects, tasks, statuses, users, comments, and relations.
- Provider adapters for workspace/project/task CRUD where provider APIs allow it.
- Jira relation CRUD for core relation types:
  - `relates`;
  - `blocks`;
  - `contains` through Jira hierarchy by default or custom issue link mapping.
- Yandex Tracker relation CRUD for core relation types:
  - `relates`;
  - `blocks`;
  - `contains`.
- Configurable Jira relation mapping through explicit `RelationMappingConfig`.
- Optional env-based relation mapping helper for examples, tests, and host services that intentionally use process environment settings.
- Manual example flows for Jira, Yandex Tracker, and Asana inspection.

### Validated manually
- Yandex Tracker relation flow: four tasks and three different relations from the root task.
- Jira relation flow on `https://jira.evt-s.ru/`: four tasks and three different relations from the root task, with custom `contains` mapping when a suitable Jira link type is configured.

## Design principles
- Primary configuration path: construct explicit config objects and pass them into `TrackerClient`.
- Environment variables are only an optional transport for configuration in examples, tests, or host applications.
- Public relation taxonomy stays product-first and intentionally small:
  - `relates`;
  - `blocks`;
  - `contains`.
- Provider-specific relation variants such as duplicates, clones, epics, and custom hierarchy levels are not public core relation types.
- Unsupported provider operations should fail with `ProviderCapabilityError`, not with SDK-specific exceptions.

## Near-term plan

### 1. Stabilize relation CRUD
- Add targeted automated tests for Jira and Yandex relation mapping policies.
- Add tests for `RelationMappingConfig` explicit construction and env helper parsing.
- Decide how to represent relation IDs consistently when a provider needs additional deletion context.
- Document Jira `contains` trade-offs:
  - structural hierarchy is the default;
  - custom link mapping is required for full generic create/delete behavior.

### 2. Improve examples as manual integration checks
- Keep examples safe by creating isolated temporary data where possible.
- Keep examples explicit about cleanup behavior and provider limitations.
- Avoid private debug access in examples unless it is clearly marked as diagnostics.

### 3. Capability transparency
- Add a provider capability table to the main README.
- Keep users/comments in the shared contract as future capabilities, but document that current adapters do not implement them yet.
- Add capability-oriented tests for unsupported operations.

### 4. Asana relation support
- Design relation support around Asana dependencies and subtasks.
- Map Asana dependencies to `blocks` only when direction can be normalized safely.
- Map Asana subtasks to `contains`.
- Do not force `relates` if there is no reliable native equivalent.

## Future provider candidates

### Committed future focus

1. **Asana relations**
   - Asana is already supported for workspace/project/task operations.
   - Next step is relation support around dependencies and subtasks.
   - Expected mapping:
     - dependencies / dependents -> `blocks`;
     - subtasks -> `contains`;
     - no forced `relates` mapping unless a reliable native equivalent is found.

2. **Bitrix24**
   - Very common in Russian companies as a broad collaboration, task, and CRM platform.
   - Has an open REST API for tasks, including modern `tasks.task.*` methods.
   - Good future provider for Russian-market coverage, but it may require careful mapping because Bitrix24 is broader than a pure task tracker.

3. **Trello**
   - Simple and widely understood board/card model.
   - Good candidate for lightweight teams and simple project boards.
   - Relation model is weak, so the first version may focus on workspaces/projects/tasks and treat relations as limited or unsupported.

### Later candidates to consider
- **Kaiten**: strong Jira alternative for Agile, Kanban, Scrum, and product teams in Russia.
- **YouGile**: common in Russian SMB and operations-heavy teams.
- **Planfix**: popular in business-process automation and service operations.
- **WEEEK**: useful for small teams, marketing, agencies, and lightweight project management workflows.
- **GitHub Issues**: useful for developer-centric teams; simple project/task mapping, limited relation semantics.
- **GitLab Issues**: useful where source control and issues are tightly coupled; relation and epic support may be useful.
- **Linear**: strong product-engineering workflow; relation semantics likely map well.
- **ClickUp**: broad task/project model; useful but can require provider-specific normalization.

## Suggested provider implementation order

1. Finish Jira/Yandex relation tests and docs.
2. Add Asana relations.
3. Add Bitrix24.
4. Add Trello.
5. Revisit Kaiten, YouGile, Planfix, or developer-tool providers based on customer demand.

## Not planned yet
- Full provider-native relation taxonomy in the public model.
- Automatic `.env` loading inside the library.
- Provider-specific SDK objects in public return models.
- Silent fallbacks for unsupported provider capabilities.
