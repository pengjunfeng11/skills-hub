from fastapi import HTTPException, status

from app.models.user import User
from app.models.skill import Skill


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def get_user_team_ids(user: User) -> set:
    """Get set of team IDs the user belongs to."""
    return {tm.team_id for tm in (user.team_memberships or [])}


def check_skill_access(skill: Skill, user: User):
    """Check if user can view this skill."""
    if skill.visibility == "public":
        return
    if skill.author_id == user.id:
        return
    if skill.visibility == "team" and skill.team_id:
        user_team_ids = get_user_team_ids(user)
        if skill.team_id in user_team_ids:
            return
    if user.role == "admin":
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def check_skill_edit(skill: Skill, user: User):
    """Check if user can edit this skill."""
    if skill.author_id == user.id:
        return
    if user.role == "admin":
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this skill")
