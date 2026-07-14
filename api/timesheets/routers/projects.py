from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from timesheets.deps import CurrentUser, DbSession
from timesheets.errors import ValidationFailed
from timesheets.models import Client, Project, TimeEntry
from timesheets.routers.common import get_owned
from timesheets.schemas.projects import ProjectIn, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _with_usage(db, projects: list[Project]) -> list[Project]:
    """Attach the total tracked seconds to each project in one query."""
    if not projects:
        return projects
    seconds = func.sum(func.extract("epoch", TimeEntry.ended_at - TimeEntry.started_at))
    rows = db.execute(
        select(TimeEntry.project_id, seconds)
        .where(
            TimeEntry.project_id.in_([p.id for p in projects]),
            TimeEntry.ended_at.is_not(None),
        )
        .group_by(TimeEntry.project_id)
    ).all()
    used = {project_id: int(total or 0) for project_id, total in rows}
    for project in projects:
        project.used_seconds = used.get(project.id, 0)
    return projects


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
    return _with_usage(db, list(db.scalars(stmt)))


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectIn, db: DbSession, user: CurrentUser) -> Project:
    client = get_owned(db, Client, body.client_id, user, "Client")
    if client.archived_at is not None:
        raise ValidationFailed("Cannot add projects to an archived client")
    project = Project(user_id=user.id, **body.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return _with_usage(db, [project])[0]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: DbSession, user: CurrentUser) -> Project:
    return _with_usage(db, [get_owned(db, Project, project_id, user, "Project")])[0]


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, body: ProjectUpdate, db: DbSession, user: CurrentUser
) -> Project:
    project = get_owned(db, Project, project_id, user, "Project")
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None and field not in ("hourly_rate", "budget_hours"):
            continue
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return _with_usage(db, [project])[0]


@router.post("/{project_id}/archive", response_model=ProjectOut)
def archive_project(project_id: int, db: DbSession, user: CurrentUser) -> Project:
    project = get_owned(db, Project, project_id, user, "Project")
    if project.archived_at is None:
        now = datetime.now(UTC)
        project.archived_at = now
        # A timer left running on an archived project could never be edited again.
        running = db.scalar(
            select(TimeEntry).where(
                TimeEntry.project_id == project.id, TimeEntry.ended_at.is_(None)
            )
        )
        if running is not None:
            running.ended_at = now
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
