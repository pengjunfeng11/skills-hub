import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    team_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
