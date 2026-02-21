from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import check_skill_access, check_skill_edit
from app.core.security import get_current_user
from app.database import get_db
from app.models.skill import Skill, SkillFile, SkillVersion
from app.models.user import User
from app.schemas.skill import (
    ParseSkillRequest,
    ParsedSkillResponse,
    SkillCreate,
    SkillListResponse,
    SkillResponse,
    SkillUpdate,
    VersionCreate,
    VersionResponse,
)
from app.utils.skill_parser import parse_skill_md, validate_semver, validate_skill_name

router = APIRouter(prefix="/api/skills", tags=["skills"])


def _escape_like(s: str) -> str:
    """Escape special characters for SQL LIKE."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _skill_to_response(skill: Skill, latest_version: str | None = None) -> SkillResponse:
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        display_name=skill.display_name,
        description=skill.description,
        tags=skill.tags or [],
        visibility=skill.visibility,
        is_published=skill.is_published,
        author_id=skill.author_id,
        team_id=skill.team_id,
        category_id=skill.category_id,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        latest_version=latest_version,
    )


@router.get("", response_model=SkillListResponse)
async def list_skills(
    q: str | None = None,
    tag: str | None = None,
    visibility: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Skill)

    # Filter by visibility: show public, user's own, and team skills
    conditions = [Skill.visibility == "public", Skill.author_id == user.id]
    if user.team_id:
        conditions.append((Skill.visibility == "team") & (Skill.team_id == user.team_id))
    if user.role == "admin":
        conditions = []  # admin sees all
        query = select(Skill)
    else:
        query = query.where(or_(*conditions))

    if q:
        escaped_q = _escape_like(q)
        query = query.where(
            or_(Skill.name.ilike(f"%{escaped_q}%"), Skill.display_name.ilike(f"%{escaped_q}%"), Skill.description.ilike(f"%{escaped_q}%"))
        )
    if tag:
        query = query.where(Skill.tags.contains([tag]))
    if visibility:
        query = query.where(Skill.visibility == visibility)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Skill.updated_at.desc()).offset((page - 1) * size).limit(size)
    query = query.options(selectinload(Skill.versions))
    result = await db.execute(query)
    skills = result.scalars().all()

    items = []
    for skill in skills:
        latest = skill.versions[0].version if skill.versions else None
        items.append(_skill_to_response(skill, latest))

    return SkillListResponse(items=items, total=total)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not validate_skill_name(data.name):
        raise HTTPException(status_code=400, detail="Skill name must be kebab-case")

    existing = await db.execute(select(Skill).where(Skill.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Skill name already exists")

    skill = Skill(
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        category_id=data.category_id,
        tags=data.tags,
        visibility=data.visibility.value if hasattr(data.visibility, 'value') else data.visibility,
        author_id=user.id,
        team_id=user.team_id,
    )
    db.add(skill)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Skill name already exists")
    await db.refresh(skill)
    return _skill_to_response(skill)


@router.post("/parse-skill-md", response_model=ParsedSkillResponse)
async def parse_skill_content(
    data: ParseSkillRequest,
    user: User = Depends(get_current_user),
):
    parsed = parse_skill_md(data.content)
    return ParsedSkillResponse(
        name=parsed.get("name"),
        display_name=parsed.get("display_name"),
        description=parsed.get("description"),
        tags=parsed.get("tags", []),
        category=parsed.get("category"),
        version=parsed.get("metadata", {}).get("version"),
        body=parsed.get("body"),
    )


@router.get("/{name}", response_model=SkillResponse)
async def get_skill(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.versions)))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_access(skill, user)
    latest = skill.versions[0].version if skill.versions else None
    return _skill_to_response(skill, latest)


@router.put("/{name}", response_model=SkillResponse)
async def update_skill(
    name: str,
    data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_edit(skill, user)

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "visibility" and hasattr(value, "value"):
            value = value.value
        setattr(skill, field, value)

    await db.commit()
    await db.refresh(skill)
    return _skill_to_response(skill)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_edit(skill, user)
    await db.delete(skill)
    await db.commit()


# --- Versions ---


@router.post("/{name}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    name: str,
    data: VersionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_edit(skill, user)

    if not validate_semver(data.version):
        raise HTTPException(status_code=400, detail="Invalid semver format")

    # Check duplicate version
    existing = await db.execute(
        select(SkillVersion).where(SkillVersion.skill_id == skill.id, SkillVersion.version == data.version)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Version already exists")

    version = SkillVersion(
        skill_id=skill.id,
        version=data.version,
        content=data.content,
        changelog=data.changelog,
        metadata_json=data.metadata_json,
        published_at=datetime.now(timezone.utc),
    )
    db.add(version)
    await db.flush()  # ensure version.id is available for FK references

    # Add files if provided
    if data.files:
        for path, content in data.files.items():
            # Normalize and check for path traversal
            import posixpath
            normalized = posixpath.normpath(path)
            if normalized.startswith("/") or normalized.startswith("..") or "/../" in normalized:
                raise HTTPException(status_code=400, detail=f"Invalid file path: {path}")
            skill_file = SkillFile(
                skill_version_id=version.id,
                path=normalized,
                content=content,
                file_type=path.rsplit(".", 1)[-1] if "." in path else None,
            )
            db.add(skill_file)

    skill.is_published = True
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Version already exists")
    await db.refresh(version)

    files_dict = {}
    if data.files:
        result = await db.execute(select(SkillFile).where(SkillFile.skill_version_id == version.id))
        for f in result.scalars().all():
            files_dict[f.path] = f.content

    return VersionResponse(
        id=version.id,
        skill_id=version.skill_id,
        version=version.version,
        content=version.content,
        changelog=version.changelog,
        metadata_json=version.metadata_json,
        created_at=version.created_at,
        published_at=version.published_at,
        files=files_dict,
    )


@router.get("/{name}/versions", response_model=list[VersionResponse])
async def list_versions(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_access(skill, user)

    result = await db.execute(
        select(SkillVersion)
        .where(SkillVersion.skill_id == skill.id)
        .order_by(SkillVersion.created_at.desc())
    )
    versions = result.scalars().all()
    return [
        VersionResponse(
            id=v.id,
            skill_id=v.skill_id,
            version=v.version,
            content=v.content,
            changelog=v.changelog,
            metadata_json=v.metadata_json,
            created_at=v.created_at,
            published_at=v.published_at,
        )
        for v in versions
    ]


@router.get("/{name}/versions/{ver}", response_model=VersionResponse)
async def get_version(
    name: str,
    ver: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_access(skill, user)

    result = await db.execute(
        select(SkillVersion)
        .where(SkillVersion.skill_id == skill.id, SkillVersion.version == ver)
        .options(selectinload(SkillVersion.files))
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    files_dict = {f.path: f.content for f in version.files}
    return VersionResponse(
        id=version.id,
        skill_id=version.skill_id,
        version=version.version,
        content=version.content,
        changelog=version.changelog,
        metadata_json=version.metadata_json,
        created_at=version.created_at,
        published_at=version.published_at,
        files=files_dict,
    )
