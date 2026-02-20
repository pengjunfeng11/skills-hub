from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin
from app.core.security import get_current_user
from app.database import get_db
from app.models.team import Team
from app.models.user import User
from app.schemas.skill import TeamCreate, TeamResponse

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.execute(select(Team).where(Team.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Team slug already exists")

    team = Team(name=data.name, slug=data.slug, description=data.description)
    db.add(team)
    await db.commit()
    await db.refresh(team)

    # Add creator to team
    user.team_id = team.id
    await db.commit()

    return team


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).order_by(Team.name))
    return result.scalars().all()


@router.get("/{slug}", response_model=TeamResponse)
async def get_team(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).where(Team.slug == slug))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
