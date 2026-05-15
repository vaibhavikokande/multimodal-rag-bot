from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.crud.workspace import (
    create_workspace, get_workspace, get_workspaces_by_user,
    update_workspace, delete_workspace, add_member, remove_member
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None


class InviteMemberRequest(BaseModel):
    user_email: str
    role: str = "member"


@router.post("/")
async def create_new_workspace(
    request: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    import re
    slug = request.slug or re.sub(r"[^a-z0-9-]", "-", request.name.lower()).strip("-")

    workspace = await create_workspace(
        db=db,
        name=request.name,
        description=request.description,
        slug=slug,
        owner_id=current_user.id,
    )
    return _workspace_dict(workspace)


@router.get("/")
async def list_workspaces(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_by_user(db, current_user.id)
    return {"workspaces": [_workspace_dict(w) for w in workspaces]}


@router.get("/{workspace_id}")
async def get_workspace_detail(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return _workspace_dict(workspace)


@router.put("/{workspace_id}")
async def update_workspace_settings(
    workspace_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    workspace = await update_workspace(db, workspace_id, update_data)
    return _workspace_dict(workspace)


@router.post("/{workspace_id}/members")
async def invite_member(
    workspace_id: int,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    from app.crud.user import get_user_by_email
    user = await get_user_by_email(db, request.user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await add_member(db, workspace_id, user.id, request.role)
    return {"message": f"{request.user_email} added to workspace"}


@router.delete("/{workspace_id}/members/{user_id}")
async def kick_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_member(db, workspace_id, user_id)
    return {"message": "Member removed"}


def _workspace_dict(w) -> dict:
    return {
        "id": w.id,
        "name": w.name,
        "description": w.description,
        "slug": w.slug,
        "logo_url": w.logo_url,
        "owner_id": w.owner_id,
        "is_active": w.is_active,
        "created_at": str(w.created_at),
    }
