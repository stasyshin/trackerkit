import asyncio
import os
import random
import string

from depensee_tracker_client import (
    CreateProjectInput,
    CreateTaskInput,
    ProviderCapabilityError,
    TrackerClient,
    TrackerClientError,
    UpdateProjectInput,
    UpdateTaskInput,
    YandexTrackerAuthConfig,
)
from _base import wait_for_enter
from _env import load_env


async def main() -> None:
    """Run the Yandex Tracker example flow with explicit auth config."""

    load_env()
    cloud_org_id = os.getenv("YANDEX_CLOUD_ORG_ID")
    org_id = os.getenv("YANDEX_ORG_ID")

    # Auth config makes the expected parameters explicit for the example.
    auth_config = YandexTrackerAuthConfig(
        token=os.getenv("YANDEX_TOKEN"),
        cloud_org_id=cloud_org_id,
        org_id=None if cloud_org_id else org_id,
    )

    client = TrackerClient(
        provider="yandex_tracker",
        auth_data=auth_config.model_dump(exclude_none=True),
    )

    # 1. Check connection before any CRUD calls.
    await client.ensure_connection()
    print("yandex_tracker: connected")

    # 2. Read workspaces available for the current token.
    workspaces = await client.list_workspaces()
    print(workspaces)

    projects = await client.list_projects()
    print("yandex_tracker: available projects")
    for available_project in projects:
        print(
            f"- id={available_project.id} key={available_project.key} "
            f"name={available_project.name}"
        )

    # 3. Reuse the first existing project when possible. Otherwise create a
    # temporary queue-backed project for the example flow.
    created_project = False
    if projects:
        project = projects[0]
        print(f"Fallback to existing Yandex project: {project.key or project.id}")
    else:
        # In Yandex Tracker the shared Project model is backed by a queue.
        # Queue key must contain latin letters only, so we keep a readable
        # prefix and add a short letter suffix for uniqueness between runs.
        project_key = "DEPENSEE" + "".join(random.choices(string.ascii_uppercase, k=3))
        try:
            project = await client.create_project(
                CreateProjectInput(
                    name=f"Depensee Demo Project {project_key[-3:]}",
                    key=project_key,
                    description="Example project created from depensee-tracker-client.",
                )
            )
            created_project = True
        except ProviderCapabilityError as error:
            print(error)
            return
    print(project)

    if created_project:
        wait_for_enter("Project created. Check it in Yandex Tracker before update.")

        # Update the created project.
        project = await client.update_project(
            project.id,
            UpdateProjectInput(description="Updated Yandex example project."),
        )
        print(project)

        wait_for_enter("Project updated. Check it in Yandex Tracker before task creation.")
    else:
        wait_for_enter("Using existing Yandex project. Check it before task creation.")

    # 4. Create a task inside the created project.
    task = await client.create_task(
        CreateTaskInput(
            title="Prepare release notes",
            description="Draft the release notes for sprint 12",
            project_id=project.key or project.id,
        )
    )
    print(task)

    # Read the created task back from the tracker to validate the round-trip
    # without printing the same payload twice in the console.
    await client.get_task(task.id)

    wait_for_enter("Task created. Check it in Yandex Tracker before update.")

    # Update the created task.
    task = await client.update_task(
        task.id,
        UpdateTaskInput(description="Updated release notes draft"),
    )
    print(task)

    if created_project:
        wait_for_enter("Task updated. Check it in Yandex Tracker before project delete.")
    else:
        wait_for_enter(
            "Task updated. It will remain in the existing Yandex project after the example run."
        )

    # Yandex Tracker does not support direct issue deletion in this flow.
    # We remove the temporary queue/project only when this example created it.
    if created_project:
        wait_for_enter(
            "Task will remain in the queue until project delete. Check it before cleanup."
        )
        await client.delete_project(project.id)
        wait_for_enter("Project deleted. Check it in Yandex Tracker after delete.")
    print("yandex_tracker: done")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except TrackerClientError as error:
        print(error)

