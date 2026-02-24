from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_api_key_with_user
from app.database import get_db
from app.models.api_key import ApiKey
from app.models.skill import Skill, SkillFile, SkillVersion
from app.models.subscription import SkillSubscription
from app.models.usage_log import SkillUsageLog
from app.models.user import User
from app.schemas.skill import (
    CatalogItem,
    CatalogResponse,
    ResolvedSkill,
    ResolveRequest,
    ResolveResponse,
)

router = APIRouter(prefix="/api/v1/skills", tags=["plugin"])


@router.post("/resolve", response_model=ResolveResponse)
async def resolve_skills(
    data: ResolveRequest,
    db: AsyncSession = Depends(get_db),
    auth: tuple[User, ApiKey] = Depends(get_api_key_with_user),
):
    """Batch resolve skills by name, optionally with version pinning."""
    user, api_key = auth

    # Get user's subscribed skill IDs (enabled only)
    sub_result = await db.execute(
        select(SkillSubscription.skill_id).where(
            SkillSubscription.user_id == user.id,
            SkillSubscription.enabled == True,
        )
    )
    subscribed_skill_ids = {row[0] for row in sub_result.all()}

    if not subscribed_skill_ids:
        return ResolveResponse(skills=[])

    resolved = []

    for spec in data.skills:
        # Parse "skill-name" or "skill-name@1.2.0"
        if "@" in spec:
            name, ver = spec.split("@", 1)
        else:
            name, ver = spec, None

        result = await db.execute(select(Skill).where(
            Skill.name == name, Skill.is_published == True
        ))
        skill = result.scalar_one_or_none()
        if not skill:
            continue

        # Subscription filtering
        if skill.id not in subscribed_skill_ids:
            continue

        # Get specific version or latest
        if ver:
            ver_result = await db.execute(
                select(SkillVersion)
                .where(SkillVersion.skill_id == skill.id, SkillVersion.version == ver)
                .options(selectinload(SkillVersion.files))
            )
        else:
            ver_result = await db.execute(
                select(SkillVersion)
                .where(SkillVersion.skill_id == skill.id)
                .order_by(SkillVersion.created_at.desc())
                .limit(1)
                .options(selectinload(SkillVersion.files))
            )

        version = ver_result.scalar_one_or_none()
        if not version:
            continue

        files_dict = {f.path: f.content for f in version.files}
        resolved.append(
            ResolvedSkill(
                name=skill.name,
                version=version.version,
                description=skill.description,
                content=version.content,
                files=files_dict,
            )
        )

        # Log usage
        db.add(SkillUsageLog(
            skill_id=skill.id,
            skill_name=skill.name,
            skill_version=version.version,
            user_id=user.id,
            api_key_id=api_key.id,
            action="resolve",
        ))

    await db.commit()
    return ResolveResponse(skills=resolved)


@router.get("/catalog", response_model=CatalogResponse)
async def catalog(
    db: AsyncSession = Depends(get_db),
    auth: tuple[User, ApiKey] = Depends(get_api_key_with_user),
):
    """List all published skills that the user is subscribed to."""
    user, api_key = auth

    # Get user's subscribed skill IDs (enabled only)
    sub_result = await db.execute(
        select(SkillSubscription.skill_id).where(
            SkillSubscription.user_id == user.id,
            SkillSubscription.enabled == True,
        )
    )
    subscribed_skill_ids = {row[0] for row in sub_result.all()}

    if not subscribed_skill_ids:
        # Log usage even when empty
        db.add(SkillUsageLog(
            skill_name="*",
            user_id=user.id,
            api_key_id=api_key.id,
            action="catalog",
        ))
        await db.commit()
        return CatalogResponse(skills=[])

    result = await db.execute(
        select(Skill)
        .where(
            Skill.is_published == True,
            Skill.id.in_(subscribed_skill_ids),
        )
        .options(selectinload(Skill.versions))
        .order_by(Skill.name)
    )
    skills = result.scalars().all()

    items = []
    for skill in skills:
        latest = skill.versions[0] if skill.versions else None
        if latest:
            items.append(
                CatalogItem(
                    name=skill.name,
                    description=skill.description,
                    version=latest.version,
                    tags=skill.tags or [],
                )
            )

    # Log usage
    db.add(SkillUsageLog(
        skill_name="*",
        user_id=user.id,
        api_key_id=api_key.id,
        action="catalog",
    ))
    await db.commit()

    return CatalogResponse(skills=items)


@router.get("/{name}/raw")
async def get_skill_raw(
    name: str,
    version: str | None = None,
    db: AsyncSession = Depends(get_db),
    auth: tuple[User, ApiKey] = Depends(get_api_key_with_user),
):
    """Get raw SKILL.md content for a skill."""
    user, api_key = auth

    result = await db.execute(select(Skill).where(
        Skill.name == name, Skill.is_published == True
    ))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Subscription check
    sub_result = await db.execute(
        select(SkillSubscription).where(
            SkillSubscription.user_id == user.id,
            SkillSubscription.skill_id == skill.id,
            SkillSubscription.enabled == True,
        )
    )
    if not sub_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not subscribed to this skill")

    if version:
        ver_result = await db.execute(
            select(SkillVersion).where(SkillVersion.skill_id == skill.id, SkillVersion.version == version)
        )
    else:
        ver_result = await db.execute(
            select(SkillVersion)
            .where(SkillVersion.skill_id == skill.id)
            .order_by(SkillVersion.created_at.desc())
            .limit(1)
        )

    ver = ver_result.scalar_one_or_none()
    if not ver:
        raise HTTPException(status_code=404, detail="No version found")

    # Log usage
    db.add(SkillUsageLog(
        skill_id=skill.id,
        skill_name=skill.name,
        skill_version=ver.version,
        user_id=user.id,
        api_key_id=api_key.id,
        action="raw",
    ))
    await db.commit()

    return {"name": skill.name, "version": ver.version, "content": ver.content}
