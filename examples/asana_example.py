import asyncio
import os

from depensee_tracker_client import (
    AsanaAuthConfig,
    TaskQuery,
    TrackerClient,
    TrackerClientError,
)
from _env import load_env


async def main() -> None:
    """Run the Asana example flow with explicit auth config."""

    load_env()

    # Auth config makes the expected parameters explicit for the example.
    auth_config = AsanaAuthConfig(
        access_token=os.getenv("ASANA_TOKEN"),
    )

    client = TrackerClient(
        provider="asana",
        auth_data=auth_config.model_dump(exclude_none=True),
    )

    await client.ensure_connection()
    print("asana: connected")

    workspaces = await client.list_workspaces()
    print(workspaces)

    projects = await client.list_projects()
    print(projects)

    project_id = os.getenv("ASANA_PROJECT_ID")
    if not project_id:
        print("Skip task listing. Set ASANA_PROJECT_ID to inspect Asana tasks.")
        return

    tasks = await client.list_tasks(TaskQuery(project_id=project_id))
    print(tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except TrackerClientError as error:
        print(error)

