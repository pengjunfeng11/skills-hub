from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_api_key_user
from app.database import get_db
from app.models.skill import Skill, SkillFile, SkillVersion
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
    user: User = Depends(get_api_key_user),
):
    """Batch resolve skills by name, optionally with version pinning."""
    resolved = []

    for spec in data.skills:
        # Parse "skill-name" or "skill-name@1.2.0"
        if "@" in spec:
            name, ver = spec.split("@", 1)
        else:
            name, ver = spec, None

        result = await db.execute(select(Skill).where(Skill.name == name, Skill.is_published == True))
        skill = result.scalar_one_or_none()
        if not skill:
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

    return ResolveResponse(skills=resolved)


@router.get("/catalog", response_model=CatalogResponse)
async def catalog(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_api_key_user),
):
    """List all published skills with their latest version."""
    result = await db.execute(
        select(Skill)
        .where(Skill.is_published == True, Skill.visibility == "public")
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

    return CatalogResponse(skills=items)


@router.get("/{name}/raw")
async def get_skill_raw(
    name: str,
    version: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_api_key_user),
):
    """Get raw SKILL.md content for a skill."""
    result = await db.execute(select(Skill).where(Skill.name == name, Skill.is_published == True))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

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

    return {"name": skill.name, "version": ver.version, "content": ver.content}
