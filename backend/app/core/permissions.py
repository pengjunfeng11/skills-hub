from fastapi import HTTPException, status

from app.models.user import User
from app.models.skill import Skill


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def check_skill_access(skill: Skill, user: User):
    """Check if user can view this skill."""
    if skill.visibility == "public":
        return
    if skill.author_id == user.id:
        return
    if skill.visibility == "team" and skill.team_id and user.team_id == skill.team_id:
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
