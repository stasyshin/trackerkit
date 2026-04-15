from depensee_tracker_client.contracts.comments import CommentCapability
from depensee_tracker_client.contracts.connection import ConnectionCapability
from depensee_tracker_client.contracts.projects import (
    ProjectReadCapability,
    ProjectWriteCapability,
    WorkspaceCapability,
)
from depensee_tracker_client.contracts.relations import RelationCapability
from depensee_tracker_client.contracts.tasks import TaskReadCapability, TaskWriteCapability
from depensee_tracker_client.contracts.users import UserCapability


class TaskTrackerClient(
    ConnectionCapability,
    TaskReadCapability,
    TaskWriteCapability,
    WorkspaceCapability,
    ProjectReadCapability,
    ProjectWriteCapability,
    UserCapability,
    CommentCapability,
    RelationCapability,
):
    """Unified async port composed from small capability contracts."""

