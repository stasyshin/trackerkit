import asyncio
import os

from depensee_tracker_client import (
    CreateRelationInput,
    CreateProjectInput,
    CreateTaskInput,
    JiraAuthConfig,
    ProviderCapabilityError,
    RelationType,
    TaskQuery,
    TrackerClient,
    TrackerClientError,
    UpdateProjectInput,
    UpdateRelationInput,
    UpdateTaskInput,
)
from _base import wait_for_enter
from _env import load_env


async def main() -> None:
    """Run the Jira example flow with explicit auth config."""

    load_env()

    # Auth config makes the expected parameters explicit for the example.
    auth_config = JiraAuthConfig(
        base_url=os.getenv("JIRA_BASE_URL"),
        access_token=os.getenv("JIRA_TOKEN"),
    )

    client = TrackerClient(
        provider="jira",
        auth_data=auth_config.model_dump(exclude_none=True),
    )

    # 1. Check connection before any CRUD calls.
    await client.ensure_connection()
    print("jira: connected")

    # 2. Read workspaces available for the current token.
    workspaces = await client.list_workspaces()
    print(workspaces)

    available_projects = await client.list_projects()
    print("jira: available projects")
    for available_project in available_projects:
        print(
            f"- id={available_project.id} key={available_project.key} "
            f"name={available_project.name}"
        )

    # 3. Create, read, update, and delete a project when the token has enough
    # permissions. Otherwise, fall back to the first existing project so the
    # task flow can still be verified on restricted Jira instances.
    created_project = False
    try:
        project = await client.create_project(
            CreateProjectInput(
                name="Platform",
                key="PLATFORM",
                description="Platform team project",
            )
        )
        created_project = True
    except ProviderCapabilityError as error:
        print(error)
        if not available_projects:
            print("No existing Jira projects available for fallback task flow.")
            return
        project = available_projects[0]
        print(f"Fallback to existing Jira project: {project.key or project.id}")

    print(project)
    await client.get_project(project.id)

    if created_project:
        wait_for_enter("Project created. Check it in Jira before update.")

        project = await client.update_project(
            project.id,
            UpdateProjectInput(description="Updated description"),
        )
        print(project)

        wait_for_enter("Project updated. Check it in Jira before task creation.")
    else:
        wait_for_enter("Using existing Jira project. Check it before task creation.")

    # 4. Create three tasks for a simple visible relation lifecycle in Jira.
    project_id = project.id
    tasks = await client.list_tasks(TaskQuery(project_id=project_id))
    print(tasks)

    created_tasks = []
    for index, title in enumerate(
        (
            "Prepare release notes",
            "Review release notes",
            "Publish release summary",
        ),
        start=1,
    ):
        task = await client.create_task(
            CreateTaskInput(
                title=title,
                description=f"Example Jira task {index} created for relation CRUD validation.",
                project_id=project_id,
            )
        )
        created_tasks.append(task)
        print(task)

    await client.get_task(created_tasks[0].id)
    wait_for_enter("Tasks created. Check them in Jira before task update.")

    created_tasks[0] = await client.update_task(
        created_tasks[0].id,
        UpdateTaskInput(description="Updated Jira relation example root task."),
    )
    print(created_tasks[0])

    wait_for_enter("Task updated. Check it in Jira before relation creation.")

    root_task, blocked_task, related_task = created_tasks

    relation = await client.create_relation(
        CreateRelationInput(
            source_task_id=root_task.id,
            target_task_id=blocked_task.id,
            relation_type=RelationType.BLOCKS,
        )
    )
    print("jira: created relation")
    print(relation)
    jira_transport = client._client._transport
    print("jira: raw create_issue_link response")
    print(jira_transport.get_last_issue_link_debug())

    print("jira: relations for root task")
    print(await client.list_relations(root_task.id))
    print("jira: relations for blocked task")
    print(await client.list_relations(blocked_task.id))

    if relation.id is not None:
        wait_for_enter("Relation created. Check it in Jira before relation update.")
        relation = await client.update_relation(
            relation.id,
            UpdateRelationInput(
                source_task_id=root_task.id,
                target_task_id=related_task.id,
                relation_type=RelationType.RELATES,
            ),
        )
        print("jira: updated relation")
        print(relation)
        print("jira: raw create_issue_link response after update")
        print(jira_transport.get_last_issue_link_debug())
        print("jira: relations for root task after update")
        print(await client.list_relations(root_task.id))
        print("jira: relations for related task after update")
        print(await client.list_relations(related_task.id))
    else:
        print("Skip Jira relation update because provider did not return relation id.")

    wait_for_enter("Check Jira before relation cleanup.")

    if relation.id is not None:
        await client.delete_relation(relation.id)

    wait_for_enter("Relation deleted. Check Jira before task delete.")

    for task in reversed(created_tasks):
        await client.delete_task(task.id)
    wait_for_enter("Tasks deleted. Check them in Jira after delete.")

    if created_project:
        wait_for_enter("Check the project in Jira before project delete.")
        await client.delete_project(project.id)
        wait_for_enter("Project deleted. Check it in Jira after delete.")
    print("jira: done")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except TrackerClientError as error:
        print(error)

