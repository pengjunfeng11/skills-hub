import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import check_skill_access, check_skill_edit, get_user_team_ids
from app.core.security import get_current_user
from app.database import get_db
from app.models.edit_log import SkillEditLog
from app.models.skill import Skill, SkillFile, SkillVersion, SkillVisibilityTeam
from app.models.subscription import SkillSubscription
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.skill import (
    ParseSkillRequest,
    ParsedSkillResponse,
    SkillCreate,
    SkillEditLogResponse,
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


def _dump_detail(payload: dict | None) -> str | None:
    if not payload:
        return None
    return json.dumps(payload, ensure_ascii=False)


async def _append_edit_log(
    db: AsyncSession,
    *,
    skill_id,
    user: User | None,
    action: str,
    target_type: str = "skill",
    target_path: str | None = None,
    from_version: str | None = None,
    to_version: str | None = None,
    detail: dict | None = None,
):
    db.add(
        SkillEditLog(
            skill_id=skill_id,
            actor_user_id=user.id if user else None,
            action=action,
            target_type=target_type,
            target_path=target_path,
            from_version=from_version,
            to_version=to_version,
            detail=_dump_detail(detail),
        )
    )


def _skill_to_response(
    skill: Skill,
    latest_version: str | None = None,
    is_subscribed: bool | None = None,
    subscription_enabled: bool | None = None,
    author_username: str | None = None,
) -> SkillResponse:
    team_ids = [rel.team_id for rel in (skill.visibility_teams or [])]
    if not team_ids and skill.team_id:
        team_ids = [skill.team_id]
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        display_name=skill.display_name,
        description=skill.description,
        tags=skill.tags or [],
        visibility=skill.visibility,
        is_published=skill.is_published,
        author_id=skill.author_id,
        author_username=author_username or (skill.author.username if skill.author else None),
        team_id=skill.team_id,
        team_ids=team_ids,
        category_id=skill.category_id,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        latest_version=latest_version,
        is_subscribed=is_subscribed,
        subscription_enabled=subscription_enabled,
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

    # Filter by visibility: show public, user's own, and team skills (multi-team)
    user_team_ids = get_user_team_ids(user)
    conditions = [Skill.visibility == "public", Skill.author_id == user.id]
    if user_team_ids:
        team_visible_skill_ids = (
            select(SkillVisibilityTeam.skill_id)
            .where(SkillVisibilityTeam.team_id.in_(user_team_ids))
        )
        conditions.append((Skill.visibility == "team") & Skill.id.in_(team_visible_skill_ids))
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
    query = query.options(selectinload(Skill.versions), selectinload(Skill.author), selectinload(Skill.visibility_teams))
    result = await db.execute(query)
    skills = result.scalars().all()

    # Batch fetch subscriptions for these skills
    skill_ids = [s.id for s in skills]
    sub_map = {}
    if skill_ids:
        sub_result = await db.execute(
            select(SkillSubscription).where(
                SkillSubscription.user_id == user.id,
                SkillSubscription.skill_id.in_(skill_ids),
            )
        )
        for sub in sub_result.scalars().all():
            sub_map[sub.skill_id] = sub

    items = []
    for skill in skills:
        latest = skill.versions[0].version if skill.versions else None
        sub = sub_map.get(skill.id)
        items.append(_skill_to_response(
            skill,
            latest,
            is_subscribed=sub is not None if sub_map is not None else None,
            subscription_enabled=sub.enabled if sub else None,
        ))

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

    visibility_value = data.visibility.value if hasattr(data.visibility, "value") else data.visibility
    requested_team_ids = list(dict.fromkeys(data.team_ids or ([] if data.team_id is None else [data.team_id])))
    if visibility_value == "team":
        user_team_ids = get_user_team_ids(user)
        for tid in requested_team_ids:
            if tid not in user_team_ids:
                raise HTTPException(status_code=403, detail="You are not a member of one or more selected teams")
        if not requested_team_ids:
            raise HTTPException(status_code=400, detail="Team visibility requires team_ids")
    else:
        # For public/private, ignore team scope to avoid stale team_ids leakage.
        requested_team_ids = []
    team_id = requested_team_ids[0] if requested_team_ids else None

    skill = Skill(
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        category_id=data.category_id,
        tags=data.tags,
        visibility=visibility_value,
        author_id=user.id,
        team_id=team_id,
    )
    db.add(skill)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Skill name already exists")

    if requested_team_ids:
        for tid in requested_team_ids:
            db.add(SkillVisibilityTeam(skill_id=skill.id, team_id=tid))

    # Auto-subscribe the author
    subscription = SkillSubscription(user_id=user.id, skill_id=skill.id, enabled=True)
    db.add(subscription)
    await _append_edit_log(
        db,
        skill_id=skill.id,
        user=user,
        action="skill_created",
        detail={
            "display_name": skill.display_name,
            "visibility": skill.visibility,
            "team_ids": [str(tid) for tid in requested_team_ids],
            "tags": skill.tags or [],
        },
    )

    await db.commit()
    created_result = await db.execute(
        select(Skill).where(Skill.id == skill.id).options(selectinload(Skill.visibility_teams), selectinload(Skill.author))
    )
    created_skill = created_result.scalar_one()
    return _skill_to_response(created_skill, is_subscribed=True, subscription_enabled=True, author_username=user.username)


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
    result = await db.execute(
        select(Skill)
        .where(Skill.name == name)
        .options(selectinload(Skill.versions), selectinload(Skill.author), selectinload(Skill.visibility_teams))
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_access(skill, user)

    # Check subscription
    sub_result = await db.execute(
        select(SkillSubscription).where(
            SkillSubscription.user_id == user.id,
            SkillSubscription.skill_id == skill.id,
        )
    )
    sub = sub_result.scalar_one_or_none()

    latest = skill.versions[0].version if skill.versions else None
    return _skill_to_response(
        skill, latest,
        is_subscribed=sub is not None,
        subscription_enabled=sub.enabled if sub else None,
    )


@router.put("/{name}", response_model=SkillResponse)
async def update_skill(
    name: str,
    data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.visibility_teams)))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_edit(skill, user)

    incoming = data.model_dump(exclude_unset=True)
    new_visibility = incoming.get("visibility")
    if hasattr(new_visibility, "value"):
        new_visibility = new_visibility.value
    target_visibility = new_visibility if new_visibility is not None else skill.visibility

    if target_visibility == "team":
        user_team_ids = get_user_team_ids(user)
        if "team_ids" in incoming and incoming["team_ids"] is not None:
            normalized_team_ids = list(dict.fromkeys(incoming["team_ids"]))
        elif "team_id" in incoming:
            normalized_team_ids = [] if incoming["team_id"] is None else [incoming["team_id"]]
        else:
            normalized_team_ids = [rel.team_id for rel in (skill.visibility_teams or [])]
            if not normalized_team_ids and skill.team_id:
                normalized_team_ids = [skill.team_id]

        for tid in normalized_team_ids:
            if tid not in user_team_ids:
                raise HTTPException(status_code=403, detail="You are not a member of one or more selected teams")
        if not normalized_team_ids:
            raise HTTPException(status_code=400, detail="Team visibility requires team_ids")
    else:
        # Switching away from team visibility must clear stored team scope.
        normalized_team_ids = []

    changes: dict[str, dict] = {}
    for field, value in incoming.items():
        if field == "team_ids":
            continue
        if field == "visibility" and hasattr(value, "value"):
            value = value.value
        old_value = getattr(skill, field)
        if old_value != value:
            changes[field] = {"old": old_value, "new": value}
        setattr(skill, field, value)

    old_team_ids = [rel.team_id for rel in (skill.visibility_teams or [])]
    if not old_team_ids and skill.team_id:
        old_team_ids = [skill.team_id]
    if old_team_ids != normalized_team_ids:
        changes["team_ids"] = {"old": [str(t) for t in old_team_ids], "new": [str(t) for t in normalized_team_ids]}
        skill.team_id = normalized_team_ids[0] if normalized_team_ids else None
        skill.visibility_teams.clear()
        for tid in normalized_team_ids:
            skill.visibility_teams.append(SkillVisibilityTeam(skill_id=skill.id, team_id=tid))

    if changes:
        await _append_edit_log(
            db,
            skill_id=skill.id,
            user=user,
            action="skill_updated",
            detail={"changes": changes},
        )

    await db.commit()
    updated_result = await db.execute(
        select(Skill).where(Skill.id == skill.id).options(selectinload(Skill.visibility_teams), selectinload(Skill.author))
    )
    updated_skill = updated_result.scalar_one()
    return _skill_to_response(updated_skill)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.visibility_teams)))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_edit(skill, user)
    await db.delete(skill)
    await db.commit()


# --- Subscribe / Unsubscribe ---


@router.post("/{name}/subscribe", status_code=status.HTTP_200_OK)
async def subscribe_skill(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.visibility_teams)))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_access(skill, user)

    sub_result = await db.execute(
        select(SkillSubscription).where(
            SkillSubscription.user_id == user.id,
            SkillSubscription.skill_id == skill.id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if sub:
        sub.enabled = True
    else:
        sub = SkillSubscription(user_id=user.id, skill_id=skill.id, enabled=True)
        db.add(sub)

    await db.commit()
    return {"detail": "Subscribed", "enabled": True}


@router.delete("/{name}/subscribe", status_code=status.HTTP_200_OK)
async def unsubscribe_skill(
    name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.visibility_teams)))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    sub_result = await db.execute(
        select(SkillSubscription).where(
            SkillSubscription.user_id == user.id,
            SkillSubscription.skill_id == skill.id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if sub:
        sub.enabled = False
        await db.commit()

    return {"detail": "Unsubscribed", "enabled": False}


# --- Versions ---


@router.post("/{name}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    name: str,
    data: VersionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.visibility_teams)))
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

    # Snapshot previous latest version/files for change detection.
    previous_version_result = await db.execute(
        select(SkillVersion)
        .where(SkillVersion.skill_id == skill.id)
        .order_by(SkillVersion.created_at.desc())
        .limit(1)
        .options(selectinload(SkillVersion.files))
    )
    previous_version = previous_version_result.scalar_one_or_none()
    previous_files = {f.path: f.content for f in previous_version.files} if previous_version else {}

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

    new_files = data.files or {}
    from_version = previous_version.version if previous_version else None
    previous_content = previous_version.content if previous_version else None

    added_paths = [path for path in new_files if path not in previous_files]
    modified_paths = [path for path in new_files if path in previous_files and previous_files[path] != new_files[path]]
    deleted_paths = [path for path in previous_files if path not in new_files]
    skill_md_changed = previous_content != data.content

    await _append_edit_log(
        db,
        skill_id=skill.id,
        user=user,
        action="version_published",
        target_type="version",
        from_version=from_version,
        to_version=data.version,
        detail={
            "changelog": data.changelog,
            "metadata_json": data.metadata_json,
            "summary": {
                "skill_md_changed": skill_md_changed,
                "files_added": len(added_paths),
                "files_modified": len(modified_paths),
                "files_deleted": len(deleted_paths),
                "added_paths": added_paths,
                "modified_paths": modified_paths,
                "deleted_paths": deleted_paths,
            },
        },
    )

    if skill_md_changed:
        await _append_edit_log(
            db,
            skill_id=skill.id,
            user=user,
            action="skill_md_updated",
            target_type="file",
            target_path="SKILL.md",
            from_version=from_version,
            to_version=data.version,
            detail={
                "old_length": len(previous_content or ""),
                "new_length": len(data.content or ""),
            },
        )

    # File-level change logs (added/modified/deleted).
    for path in added_paths:
        await _append_edit_log(
            db,
            skill_id=skill.id,
            user=user,
            action="file_added",
            target_type="file",
            target_path=path,
            from_version=from_version,
            to_version=data.version,
            detail={"new_length": len(new_files[path])},
        )

    for path in modified_paths:
        await _append_edit_log(
            db,
            skill_id=skill.id,
            user=user,
            action="file_modified",
            target_type="file",
            target_path=path,
            from_version=from_version,
            to_version=data.version,
            detail={
                "old_length": len(previous_files[path]),
                "new_length": len(new_files[path]),
            },
        )

    for path in deleted_paths:
        await _append_edit_log(
            db,
            skill_id=skill.id,
            user=user,
            action="file_deleted",
            target_type="file",
            target_path=path,
            from_version=from_version,
            to_version=data.version,
            detail={"old_length": len(previous_files[path])},
        )

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
    result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.visibility_teams)))
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
    result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.visibility_teams)))
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


@router.get("/{name}/edit-logs", response_model=list[SkillEditLogResponse])
async def list_edit_logs(
    name: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill_result = await db.execute(select(Skill).where(Skill.name == name).options(selectinload(Skill.visibility_teams)))
    skill = skill_result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    check_skill_access(skill, user)

    result = await db.execute(
        select(SkillEditLog)
        .where(SkillEditLog.skill_id == skill.id)
        .order_by(SkillEditLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()

    actor_ids = [log.actor_user_id for log in logs if log.actor_user_id]
    actor_name_map: dict = {}
    if actor_ids:
        users_result = await db.execute(select(User.id, User.username).where(User.id.in_(actor_ids)))
        actor_name_map = {uid: uname for uid, uname in users_result.all()}

    return [
        SkillEditLogResponse(
            id=log.id,
            skill_id=log.skill_id,
            actor_user_id=log.actor_user_id,
            actor_username=actor_name_map.get(log.actor_user_id),
            action=log.action,
            target_type=log.target_type,
            target_path=log.target_path,
            from_version=log.from_version,
            to_version=log.to_version,
            detail=log.detail,
            created_at=log.created_at,
        )
        for log in logs
    ]
    if requested_team_ids:
        for tid in requested_team_ids:
            db.add(SkillVisibilityTeam(skill_id=skill.id, team_id=tid))
