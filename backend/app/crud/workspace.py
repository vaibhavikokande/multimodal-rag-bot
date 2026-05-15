from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.workspace import Workspace, WorkspaceMember


async def create_workspace(db: AsyncSession, **kwargs) -> Workspace:
    workspace = Workspace(**kwargs)
    db.add(workspace)
    await db.flush()
    # Add owner as member
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=kwargs["owner_id"],
        role="owner"
    )
    db.add(member)
    await db.commit()
    await db.refresh(workspace)
    return workspace


async def get_workspace(db: AsyncSession, workspace_id: int) -> Optional[Workspace]:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def get_workspaces_by_user(db: AsyncSession, user_id: int) -> List[Workspace]:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id, Workspace.is_active == True)
        .order_by(Workspace.created_at.desc())
    )
    return result.scalars().all()


async def update_workspace(db: AsyncSession, workspace_id: int, data: dict) -> Workspace:
    allowed = {"name", "description", "logo_url", "settings"}
    filtered = {k: v for k, v in data.items() if k in allowed}
    await db.execute(update(Workspace).where(Workspace.id == workspace_id).values(**filtered))
    await db.commit()
    return await get_workspace(db, workspace_id)


async def delete_workspace(db: AsyncSession, workspace_id: int):
    await db.execute(update(Workspace).where(Workspace.id == workspace_id).values(is_active=False))
    await db.commit()


async def add_member(db: AsyncSession, workspace_id: int, user_id: int, role: str = "member"):
    member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
    db.add(member)
    await db.commit()


async def remove_member(db: AsyncSession, workspace_id: int, user_id: int):
    await db.execute(
        delete(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
    )
    await db.commit()
