from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.usage_log import SkillUsageLog
from app.models.user import User
from app.schemas.skill import StatsOverviewResponse, StatsPopularItem, StatsTrendItem

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverviewResponse)
async def stats_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get usage statistics overview."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today_start - timedelta(days=7)

    total = (await db.execute(select(func.count()).select_from(SkillUsageLog))).scalar() or 0
    today = (await db.execute(
        select(func.count()).select_from(SkillUsageLog).where(SkillUsageLog.created_at >= today_start)
    )).scalar() or 0
    last_7d = (await db.execute(
        select(func.count()).select_from(SkillUsageLog).where(SkillUsageLog.created_at >= seven_days_ago)
    )).scalar() or 0
    active_skills = (await db.execute(
        select(func.count(func.distinct(SkillUsageLog.skill_name)))
        .select_from(SkillUsageLog)
        .where(SkillUsageLog.skill_name != "*")
    )).scalar() or 0

    return StatsOverviewResponse(
        total_calls=total,
        today_calls=today,
        week_calls=last_7d,
        active_skills=active_skills,
    )


@router.get("/popular", response_model=list[StatsPopularItem])
async def stats_popular(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get popular skills by call count."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            SkillUsageLog.skill_name,
            func.count().label("call_count"),
        )
        .where(SkillUsageLog.created_at >= since, SkillUsageLog.skill_name != "*")
        .group_by(SkillUsageLog.skill_name)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = result.all()

    total = sum(r.call_count for r in rows) if rows else 1
    return [
        StatsPopularItem(
            skill_name=r.skill_name,
            call_count=r.call_count,
            percentage=round(r.call_count / total * 100, 1),
        )
        for r in rows
    ]


@router.get("/trend", response_model=list[StatsTrendItem])
async def stats_trend(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get daily call count trend."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    date_expr = func.date(SkillUsageLog.created_at)
    result = await db.execute(
        select(
            date_expr.label("date"),
            func.count().label("call_count"),
        )
        .where(SkillUsageLog.created_at >= since)
        .group_by(date_expr)
        .order_by(date_expr)
    )
    rows = result.all()

    # Fill in missing dates with 0 — rows return date as string "YYYY-MM-DD"
    date_map = {str(r.date): r.call_count for r in rows}
    trend = []
    current = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    end = datetime.now(timezone.utc).date()
    while current <= end:
        key = current.isoformat()
        trend.append(StatsTrendItem(
            date=key,
            call_count=date_map.get(key, 0),
        ))
        current += timedelta(days=1)

    return trend
