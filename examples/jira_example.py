import asyncio
import os

from depensee_tracker_client import (
    CreateProjectInput,
    CreateTaskInput,
    JiraAuthConfig,
    ProviderCapabilityError,
    TaskQuery,
    TrackerClient,
    TrackerClientError,
    UpdateProjectInput,
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

    # 4. Create, read, update, and delete a task in the selected project.
    project_id = project.id
    tasks = await client.list_tasks(TaskQuery(project_id=project_id))
    print(tasks)

    task = await client.create_task(
        CreateTaskInput(
            title="Prepare release notes",
            description="Draft the release notes for sprint 12",
            project_id=project_id,
        )
    )
    print(task)
    await client.get_task(task.id)

    wait_for_enter("Task created. Check it in Jira before update.")

    task = await client.update_task(
        task.id,
        UpdateTaskInput(description="Updated release notes draft"),
    )
    print(task)

    wait_for_enter("Task updated. Check it in Jira before delete.")

    await client.delete_task(task.id)
    wait_for_enter("Task deleted. Check it in Jira after delete.")

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

