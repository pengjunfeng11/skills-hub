from fastapi import HTTPException, status

from app.models.user import User
from app.models.skill import Skill


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def get_user_team_ids(user: User) -> set:
    """Get set of team IDs the user belongs to."""
    return {tm.team_id for tm in (user.team_memberships or [])}


def can_access_skill(skill: Skill, user: User) -> bool:
    """Return whether user can view the skill."""
    if user.role == "admin":
        return True
    if skill.visibility == "public":
        return True
    if skill.author_id == user.id:
        return True
    if skill.visibility == "team":
        user_team_ids = get_user_team_ids(user)
        visible_team_ids = {st.team_id for st in (skill.visibility_teams or [])}
        if not visible_team_ids and skill.team_id:
            visible_team_ids = {skill.team_id}
        return bool(visible_team_ids & user_team_ids)
    return False


def check_skill_access(skill: Skill, user: User):
    """Check if user can view this skill."""
    if can_access_skill(skill, user):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def check_skill_edit(skill: Skill, user: User):
    """Check if user can edit this skill."""
    if skill.author_id == user.id:
        return
    if user.role == "admin":
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this skill")
