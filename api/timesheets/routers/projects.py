from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import ValidationFailed
from timesheets.models import Client, Project
from timesheets.routers.common import get_owned
from timesheets.schemas.projects import ProjectIn, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: DbSession,
    user: CurrentUser,
    client_id: int | None = None,
    include_archived: bool = False,
) -> list[Project]:
    stmt = (
        select(Project)
        .join(Project.client)
        .options(joinedload(Project.client))
        .where(Project.user_id == user.id)
        .order_by(Client.name, Project.name)
    )
    if client_id is not None:
        stmt = stmt.where(Project.client_id == client_id)
    if not include_archived:
        stmt = stmt.where(Project.archived_at.is_(None))
    return list(db.scalars(stmt))


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectIn, db: DbSession, user: CurrentUser) -> Project:
    client = get_owned(db, Client, body.client_id, user, "Client")
    if client.archived_at is not None:
        raise ValidationFailed("Cannot add projects to an archived client")
    project = Project(user_id=user.id, **body.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: DbSession, user: CurrentUser) -> Project:
    return get_owned(db, Project, project_id, user, "Project")


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, body: ProjectUpdate, db: DbSession, user: CurrentUser
) -> Project:
    project = get_owned(db, Project, project_id, user, "Project")
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None and field != "hourly_rate":
            continue
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/archive", response_model=ProjectOut)
def archive_project(project_id: int, db: DbSession, user: CurrentUser) -> Project:
    project = get_owned(db, Project, project_id, user, "Project")
    if project.archived_at is None:
        project.archived_at = datetime.now(UTC)
        db.commit()
    return project


@router.post("/{project_id}/restore", response_model=ProjectOut)
def restore_project(project_id: int, db: DbSession, user: CurrentUser) -> Project:
    project = get_owned(db, Project, project_id, user, "Project")
    project.archived_at = None
    db.commit()
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DbSession, user: CurrentUser) -> Response:
    project = get_owned(db, Project, project_id, user, "Project")
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
