import uuid
from datetime import datetime
from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str  # kebab-case
    display_name: str
    description: str | None = None
    category_id: uuid.UUID | None = None
    tags: list[str] = []
    visibility: str = "public"


class SkillUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    category_id: uuid.UUID | None = None
    tags: list[str] | None = None
    visibility: str | None = None


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

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    items: list[SkillResponse]
    total: int


class VersionCreate(BaseModel):
    version: str  # semver
    content: str  # SKILL.md full text
    changelog: str | None = None
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

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str] = ["read"]


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
    skills: list[str]  # ["skill-a", "skill-b@1.2.0"]


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
    name: str
    slug: str
    description: str | None = None


class TeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ParseSkillRequest(BaseModel):
    content: str


class ParsedSkillResponse(BaseModel):
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    tags: list[str] = []
    category: str | None = None
    version: str | None = None
    body: str | None = None
