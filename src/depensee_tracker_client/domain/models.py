from datetime import datetime

from pydantic import BaseModel

from depensee_tracker_client.domain.enums import Provider, RelationType


class User(BaseModel):
    id: str
    display_name: str
    email: str | None = None


class Workspace(BaseModel):
    id: str
    name: str
    key: str | None = None


class ConnectionDiagnostic(BaseModel):
    provider: Provider
    is_connected: bool
    error_kind: str | None = None
    message: str | None = None
    error_type: str | None = None


class Project(BaseModel):
    id: str
    name: str
    key: str | None = None
    description: str | None = None
    workspace_id: str | None = None


class Status(BaseModel):
    id: str
    name: str
    category: str | None = None


class Task(BaseModel):
    id: str
    key: str | None = None
    title: str
    description: str | None = None
    project_id: str | None = None
    status: Status | None = None
    assignee: User | None = None
    reporter: User | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    due_date: datetime | None = None
    url: str | None = None


class Comment(BaseModel):
    id: str
    task_id: str
    body: str
    author: User | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Relation(BaseModel):
    id: str | None = None
    source_task_id: str
    target_task_id: str
    relation_type: RelationType


class TaskQuery(BaseModel):
    project_id: str | None = None
    assignee_id: str | None = None
    status_id: str | None = None
    updated_since: datetime | None = None


class CreateTaskInput(BaseModel):
    title: str
    description: str | None = None
    project_id: str | None = None
    assignee_id: str | None = None
    status_id: str | None = None
    due_date: datetime | None = None


class UpdateTaskInput(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: str | None = None
    status_id: str | None = None
    due_date: datetime | None = None


class CreateCommentInput(BaseModel):
    task_id: str
    body: str


class CreateProjectInput(BaseModel):
    name: str
    key: str | None = None
    description: str | None = None
    workspace_id: str | None = None


class UpdateProjectInput(BaseModel):
    name: str | None = None
    key: str | None = None
    description: str | None = None


class CreateRelationInput(BaseModel):
    source_task_id: str
    target_task_id: str
    relation_type: RelationType


class UpdateRelationInput(BaseModel):
    source_task_id: str
    target_task_id: str
    relation_type: RelationType

