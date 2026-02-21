import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class VisibilityEnum(str, Enum):
    public = "public"
    team = "team"
    private = "private"


VALID_SCOPES = {"read", "write"}


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)  # kebab-case
    display_name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    category_id: uuid.UUID | None = None
    tags: list[str] = []
    visibility: VisibilityEnum = VisibilityEnum.public


class SkillUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    category_id: uuid.UUID | None = None
    tags: list[str] | None = None
    visibility: VisibilityEnum | None = None


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    description: str | None = None
    tags: list[str]
    visibility: str
    is_published: bool
    author_id: uuid.UUID
    team_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    latest_version: str | None = None


class SkillListResponse(BaseModel):
    items: list[SkillResponse]
    total: int


class VersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=50)  # semver
    content: str = Field(min_length=1, max_length=1_000_000)  # SKILL.md full text, max 1MB
    changelog: str | None = Field(None, max_length=5000)
    metadata_json: dict | None = None
    files: dict[str, str] | None = None  # path -> content


class VersionResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    version: str
    content: str
    changelog: str | None = None
    metadata_json: dict | None = None
    created_at: datetime
    published_at: datetime | None = None
    files: dict[str, str] = {}


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[Literal["read", "write"]] = ["read"]


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(ApiKeyResponse):
    key: str  # only returned on creation


# Plugin API schemas
class ResolveRequest(BaseModel):
    skills: list[str] = Field(min_length=1, max_length=50)  # ["skill-a", "skill-b@1.2.0"]


class ResolvedSkill(BaseModel):
    name: str
    version: str
    description: str | None = None
    content: str
    files: dict[str, str] = {}


class ResolveResponse(BaseModel):
    skills: list[ResolvedSkill]


class CatalogItem(BaseModel):
    name: str
    description: str | None = None
    version: str
    tags: list[str] = []


class CatalogResponse(BaseModel):
    skills: list[CatalogItem]


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class TeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ParseSkillRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1_000_000)


class ParsedSkillResponse(BaseModel):
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    tags: list[str] = []
    category: str | None = None
    version: str | None = None
    body: str | None = None
