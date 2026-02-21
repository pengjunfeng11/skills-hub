import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    team_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
