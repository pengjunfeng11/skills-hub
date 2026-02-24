from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.database import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.subscription import SkillSubscription
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import TeamCreate, TeamResponse, TeamDetailResponse, TeamMemberResponse

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
    await db.flush()

    # Creator becomes admin of the team
    membership = TeamMember(user_id=user.id, team_id=team.id, role="admin")
    db.add(membership)
    await db.commit()
    await db.refresh(team)
    return team


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).order_by(Team.name))
    return result.scalars().all()


@router.get("/my", response_model=list[TeamDetailResponse])
async def my_teams(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List teams the current user belongs to."""
    result = await db.execute(
        select(TeamMember).where(TeamMember.user_id == user.id).options(
            selectinload(TeamMember.team)
        )
    )
    memberships = result.scalars().all()

    teams = []
    for m in memberships:
        teams.append(TeamDetailResponse(
            id=m.team.id,
            name=m.team.name,
            slug=m.team.slug,
            description=m.team.description,
            created_at=m.team.created_at,
            my_role=m.role,
        ))
    return teams


@router.get("/{slug}", response_model=TeamDetailResponse)
async def get_team(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Team).where(Team.slug == slug).options(
            selectinload(Team.team_members).selectinload(TeamMember.user)
        )
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    members = []
    my_role = None
    for m in team.team_members:
        members.append(TeamMemberResponse(
            id=m.id,
            user_id=m.user_id,
            username=m.user.username,
            role=m.role,
            joined_at=m.joined_at,
        ))
        if m.user_id == user.id:
            my_role = m.role

    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        created_at=team.created_at,
        members=members,
        my_role=my_role,
    )


@router.post("/{slug}/join", response_model=TeamDetailResponse)
async def join_team(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).where(Team.slug == slug))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if already a member
    existing = await db.execute(
        select(TeamMember).where(TeamMember.user_id == user.id, TeamMember.team_id == team.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already a member of this team")

    membership = TeamMember(user_id=user.id, team_id=team.id, role="member")
    db.add(membership)
    await db.commit()

    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        created_at=team.created_at,
        my_role="member",
    )


@router.post("/{slug}/leave", status_code=status.HTTP_200_OK)
async def leave_team(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).where(Team.slug == slug))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    result = await db.execute(
        select(TeamMember).where(TeamMember.user_id == user.id, TeamMember.team_id == team.id)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member of this team")

    # If user is admin, check they're not the sole admin
    if membership.role == "admin":
        admin_count = await db.execute(
            select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.role == "admin")
        )
        admins = admin_count.scalars().all()
        if len(admins) <= 1:
            raise HTTPException(status_code=400, detail="Cannot leave: you are the only admin")

    await db.delete(membership)

    # Disable subscriptions for team-visibility skills of this team
    team_skill_ids_result = await db.execute(
        select(Skill.id).where(Skill.team_id == team.id, Skill.visibility == "team")
    )
    team_skill_ids = [row[0] for row in team_skill_ids_result.all()]
    if team_skill_ids:
        sub_result = await db.execute(
            select(SkillSubscription).where(
                SkillSubscription.user_id == user.id,
                SkillSubscription.skill_id.in_(team_skill_ids),
            )
        )
        for sub in sub_result.scalars().all():
            sub.enabled = False

    await db.commit()
    return {"detail": "Left team successfully"}


@router.delete("/{slug}/members/{user_id}", status_code=status.HTTP_200_OK)
async def remove_member(
    slug: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).where(Team.slug == slug))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check the requester is an admin of this team
    requester_membership = await db.execute(
        select(TeamMember).where(TeamMember.user_id == user.id, TeamMember.team_id == team.id)
    )
    requester = requester_membership.scalar_one_or_none()
    if not requester or requester.role != "admin":
        raise HTTPException(status_code=403, detail="Only team admins can remove members")

    import uuid as _uuid
    target_user_id = _uuid.UUID(user_id)

    target_membership = await db.execute(
        select(TeamMember).where(TeamMember.user_id == target_user_id, TeamMember.team_id == team.id)
    )
    target = target_membership.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(target)

    # Disable subscriptions for team-visibility skills
    team_skill_ids_result = await db.execute(
        select(Skill.id).where(Skill.team_id == team.id, Skill.visibility == "team")
    )
    team_skill_ids = [row[0] for row in team_skill_ids_result.all()]
    if team_skill_ids:
        sub_result = await db.execute(
            select(SkillSubscription).where(
                SkillSubscription.user_id == target_user_id,
                SkillSubscription.skill_id.in_(team_skill_ids),
            )
        )
        for sub in sub_result.scalars().all():
            sub.enabled = False

    await db.commit()
    return {"detail": "Member removed"}
