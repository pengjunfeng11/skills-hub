import asyncio
import os
import uuid

os.environ["TESTING"] = "true"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# Use SQLite for testing (async)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_header(client: AsyncClient):
    """Register a user and return auth header."""
    await client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    })
    resp = await client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def api_key_header(client: AsyncClient, auth_header: dict):
    """Create an API key and return header for plugin API."""
    resp = await client.post("/api/keys", json={"name": "test-key"}, headers=auth_header)
    key = resp.json()["key"]
    return {"Authorization": f"Bearer {key}"}


@pytest_asyncio.fixture
async def sample_skill(client: AsyncClient, auth_header: dict):
    """Create a sample skill and return its data."""
    resp = await client.post("/api/skills", json={
        "name": "test-skill",
        "display_name": "Test Skill",
        "description": "A test skill",
        "tags": ["test", "demo"],
        "visibility": "public",
    }, headers=auth_header)
    return resp.json()


@pytest_asyncio.fixture
async def sample_version(client: AsyncClient, auth_header: dict, sample_skill: dict):
    """Create a sample version for the sample skill."""
    resp = await client.post("/api/skills/test-skill/versions", json={
        "version": "1.0.0",
        "content": "# Test Skill\n\nThis is a test.",
        "changelog": "Initial release",
        "files": {
            "references/api.md": "# API Reference",
            "examples/basic.md": "# Basic Example",
        },
    }, headers=auth_header)
    return resp.json()


# ============================================================
# 1. 认证测试
# ============================================================

class TestAuth:
    """用户注册、登录、JWT 认证"""

    async def test_register(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "pass123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert data["role"] == "member"
        assert "password" not in data
        assert "password_hash" not in data

    async def test_register_duplicate_username(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "dup", "email": "a@a.com", "password": "p",
        })
        resp = await client.post("/api/auth/register", json={
            "username": "dup", "email": "b@b.com", "password": "p",
        })
        assert resp.status_code == 409

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "u1", "email": "same@test.com", "password": "p",
        })
        resp = await client.post("/api/auth/register", json={
            "username": "u2", "email": "same@test.com", "password": "p",
        })
        assert resp.status_code == 409

    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "bob", "email": "bob@test.com", "password": "secret",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "bob", "password": "secret",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert resp.json()["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "carl", "email": "carl@test.com", "password": "right",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "carl", "password": "wrong",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/api/auth/login", json={
            "username": "ghost", "password": "any",
        })
        assert resp.status_code == 401

    async def test_me(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/auth/me", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    async def test_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 401


# ============================================================
# 2. Skill CRUD 测试
# ============================================================

class TestSkillCRUD:
    """Skill 的创建、读取、更新、删除"""

    async def test_create_skill(self, client: AsyncClient, auth_header: dict):
        resp = await client.post("/api/skills", json={
            "name": "my-skill",
            "display_name": "My Skill",
            "description": "Desc",
            "tags": ["tag1"],
            "visibility": "public",
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "my-skill"
        assert data["display_name"] == "My Skill"
        assert data["tags"] == ["tag1"]
        assert data["is_published"] is False

    async def test_create_skill_invalid_name(self, client: AsyncClient, auth_header: dict):
        resp = await client.post("/api/skills", json={
            "name": "Invalid Name",
            "display_name": "Test",
        }, headers=auth_header)
        assert resp.status_code == 400

    async def test_create_skill_duplicate_name(self, client: AsyncClient, auth_header: dict):
        await client.post("/api/skills", json={
            "name": "dup-skill", "display_name": "A",
        }, headers=auth_header)
        resp = await client.post("/api/skills", json={
            "name": "dup-skill", "display_name": "B",
        }, headers=auth_header)
        assert resp.status_code == 409

    async def test_list_skills(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.get("/api/skills", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(s["name"] == "test-skill" for s in data["items"])

    async def test_list_skills_search(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.get("/api/skills?q=test", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_list_skills_tag_filter(self, client: AsyncClient, auth_header: dict, sample_skill):
        # Tag filtering uses JSON contains — works on PostgreSQL, may not on SQLite
        # Just verify the endpoint doesn't error out
        resp = await client.get("/api/skills?tag=demo", headers=auth_header)
        assert resp.status_code == 200

    async def test_get_skill(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.get("/api/skills/test-skill", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["name"] == "test-skill"

    async def test_get_skill_not_found(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/skills/nonexistent", headers=auth_header)
        assert resp.status_code == 404

    async def test_update_skill(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.put("/api/skills/test-skill", json={
            "display_name": "Updated Name",
            "tags": ["updated"],
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"
        assert resp.json()["tags"] == ["updated"]

    async def test_delete_skill(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.delete("/api/skills/test-skill", headers=auth_header)
        assert resp.status_code == 204
        # Verify deleted
        resp = await client.get("/api/skills/test-skill", headers=auth_header)
        assert resp.status_code == 404

    async def test_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/skills")
        assert resp.status_code == 401


# ============================================================
# 3. 版本管理测试
# ============================================================

class TestVersionManagement:
    """Skill 版本的创建和查询"""

    async def test_create_version(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.post("/api/skills/test-skill/versions", json={
            "version": "0.1.0",
            "content": "# V0.1.0\nContent",
            "changelog": "First version",
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["version"] == "0.1.0"
        assert data["content"] == "# V0.1.0\nContent"
        assert data["changelog"] == "First version"

    async def test_create_version_with_files(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.post("/api/skills/test-skill/versions", json={
            "version": "1.0.0",
            "content": "# Skill",
            "files": {
                "references/api.md": "# API",
                "examples/basic.md": "# Example",
            },
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert "references/api.md" in data["files"]
        assert data["files"]["references/api.md"] == "# API"

    async def test_create_version_invalid_semver(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.post("/api/skills/test-skill/versions", json={
            "version": "bad",
            "content": "x",
        }, headers=auth_header)
        assert resp.status_code == 400

    async def test_create_version_duplicate(self, client: AsyncClient, auth_header: dict, sample_skill):
        await client.post("/api/skills/test-skill/versions", json={
            "version": "1.0.0", "content": "a",
        }, headers=auth_header)
        resp = await client.post("/api/skills/test-skill/versions", json={
            "version": "1.0.0", "content": "b",
        }, headers=auth_header)
        assert resp.status_code == 409

    async def test_create_version_path_traversal(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.post("/api/skills/test-skill/versions", json={
            "version": "1.0.0",
            "content": "x",
            "files": {"../etc/passwd": "hacked"},
        }, headers=auth_header)
        assert resp.status_code == 400

    async def test_create_version_absolute_path(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.post("/api/skills/test-skill/versions", json={
            "version": "1.0.0",
            "content": "x",
            "files": {"/etc/passwd": "hacked"},
        }, headers=auth_header)
        assert resp.status_code == 400

    async def test_list_versions(self, client: AsyncClient, auth_header: dict, sample_version):
        resp = await client.get("/api/skills/test-skill/versions", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["version"] == "1.0.0"

    async def test_get_version(self, client: AsyncClient, auth_header: dict, sample_version):
        resp = await client.get("/api/skills/test-skill/versions/1.0.0", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0.0"
        assert "references/api.md" in data["files"]

    async def test_get_version_not_found(self, client: AsyncClient, auth_header: dict, sample_skill):
        resp = await client.get("/api/skills/test-skill/versions/9.9.9", headers=auth_header)
        assert resp.status_code == 404

    async def test_skill_becomes_published(self, client: AsyncClient, auth_header: dict, sample_version):
        resp = await client.get("/api/skills/test-skill", headers=auth_header)
        assert resp.json()["is_published"] is True
        assert resp.json()["latest_version"] == "1.0.0"


# ============================================================
# 4. SKILL.md 解析测试
# ============================================================

class TestSkillMdParsing:
    """SKILL.md frontmatter 解析接口"""

    async def test_parse_full_frontmatter(self, client: AsyncClient, auth_header: dict):
        content = """---
name: deploy-k8s
title: K8s Deploy Guide
description: Production deployment guide
version: 2.0.0
tags:
  - devops
  - kubernetes
category: infrastructure
---

# K8s Deployment

Steps here...
"""
        resp = await client.post("/api/skills/parse-skill-md", json={
            "content": content,
        }, headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "deploy-k8s"
        assert data["display_name"] == "K8s Deploy Guide"
        assert data["description"] == "Production deployment guide"
        assert data["version"] == "2.0.0"
        assert data["tags"] == ["devops", "kubernetes"]
        assert data["category"] == "infrastructure"
        assert "Steps here" in data["body"]

    async def test_parse_minimal_frontmatter(self, client: AsyncClient, auth_header: dict):
        resp = await client.post("/api/skills/parse-skill-md", json={
            "content": "---\ntitle: Simple\n---\nBody",
        }, headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Simple"
        assert data["name"] is None

    async def test_parse_no_frontmatter(self, client: AsyncClient, auth_header: dict):
        resp = await client.post("/api/skills/parse-skill-md", json={
            "content": "# Just markdown\nNo frontmatter",
        }, headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] is None
        assert data["tags"] == []

    async def test_parse_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/skills/parse-skill-md", json={"content": "x"})
        assert resp.status_code == 401


# ============================================================
# 5. API Key 管理测试
# ============================================================

class TestApiKeys:
    """API Key 的创建、列表、删除"""

    async def test_create_api_key(self, client: AsyncClient, auth_header: dict):
        resp = await client.post("/api/keys", json={
            "name": "my-key",
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "my-key"
        assert data["key"].startswith("skh_")
        assert data["scopes"] == ["read"]

    async def test_list_api_keys(self, client: AsyncClient, auth_header: dict):
        await client.post("/api/keys", json={"name": "key1"}, headers=auth_header)
        await client.post("/api/keys", json={"name": "key2"}, headers=auth_header)
        resp = await client.get("/api/keys", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        # Key should NOT be returned in list
        for item in data:
            assert "key" not in item or item.get("key") is None

    async def test_delete_api_key(self, client: AsyncClient, auth_header: dict):
        create_resp = await client.post("/api/keys", json={"name": "to-delete"}, headers=auth_header)
        key_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/keys/{key_id}", headers=auth_header)
        assert resp.status_code == 204

    async def test_delete_nonexistent_key(self, client: AsyncClient, auth_header: dict):
        fake_id = str(uuid.uuid4())
        resp = await client.delete(f"/api/keys/{fake_id}", headers=auth_header)
        assert resp.status_code == 404


# ============================================================
# 6. Plugin API 测试
# ============================================================

class TestPluginAPI:
    """Plugin API: resolve / catalog / raw"""

    async def test_catalog(self, client: AsyncClient, api_key_header: dict,
                           auth_header: dict, sample_version):
        resp = await client.get("/api/v1/skills/catalog", headers=api_key_header)
        assert resp.status_code == 200
        data = resp.json()
        assert any(s["name"] == "test-skill" for s in data["skills"])

    async def test_resolve_single(self, client: AsyncClient, api_key_header: dict,
                                  auth_header: dict, sample_version):
        resp = await client.post("/api/v1/skills/resolve", json={
            "skills": ["test-skill"],
        }, headers=api_key_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["skills"]) == 1
        skill = data["skills"][0]
        assert skill["name"] == "test-skill"
        assert skill["version"] == "1.0.0"
        assert "# Test Skill" in skill["content"]
        assert "references/api.md" in skill["files"]

    async def test_resolve_with_version(self, client: AsyncClient, api_key_header: dict,
                                        auth_header: dict, sample_version):
        resp = await client.post("/api/v1/skills/resolve", json={
            "skills": ["test-skill@1.0.0"],
        }, headers=api_key_header)
        assert resp.status_code == 200
        assert resp.json()["skills"][0]["version"] == "1.0.0"

    async def test_resolve_nonexistent_skill(self, client: AsyncClient, api_key_header: dict):
        resp = await client.post("/api/v1/skills/resolve", json={
            "skills": ["no-such-skill"],
        }, headers=api_key_header)
        assert resp.status_code == 200
        assert resp.json()["skills"] == []

    async def test_resolve_mixed(self, client: AsyncClient, api_key_header: dict,
                                 auth_header: dict, sample_version):
        resp = await client.post("/api/v1/skills/resolve", json={
            "skills": ["test-skill", "nonexistent"],
        }, headers=api_key_header)
        assert resp.status_code == 200
        assert len(resp.json()["skills"]) == 1

    async def test_raw(self, client: AsyncClient, api_key_header: dict,
                       auth_header: dict, sample_version):
        resp = await client.get("/api/v1/skills/test-skill/raw", headers=api_key_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test-skill"
        assert data["version"] == "1.0.0"
        assert "# Test Skill" in data["content"]

    async def test_raw_not_found(self, client: AsyncClient, api_key_header: dict):
        resp = await client.get("/api/v1/skills/nonexistent/raw", headers=api_key_header)
        assert resp.status_code == 404

    async def test_plugin_api_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/skills/catalog")
        assert resp.status_code == 401

    async def test_plugin_api_invalid_key(self, client: AsyncClient):
        resp = await client.get("/api/v1/skills/catalog",
                                headers={"Authorization": "Bearer skh_invalid"})
        assert resp.status_code == 401


# ============================================================
# 7. 团队管理测试
# ============================================================

class TestTeams:
    """团队的创建和查询"""

    async def test_create_team(self, client: AsyncClient, auth_header: dict):
        resp = await client.post("/api/teams", json={
            "name": "Backend Team",
            "slug": "backend",
            "description": "Backend developers",
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Backend Team"
        assert data["slug"] == "backend"

    async def test_create_team_duplicate_slug(self, client: AsyncClient, auth_header: dict):
        await client.post("/api/teams", json={
            "name": "A", "slug": "same-slug",
        }, headers=auth_header)
        resp = await client.post("/api/teams", json={
            "name": "B", "slug": "same-slug",
        }, headers=auth_header)
        assert resp.status_code == 409

    async def test_list_teams(self, client: AsyncClient, auth_header: dict):
        await client.post("/api/teams", json={"name": "T1", "slug": "t1"}, headers=auth_header)
        resp = await client.get("/api/teams", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_team(self, client: AsyncClient, auth_header: dict):
        await client.post("/api/teams", json={"name": "T2", "slug": "t2"}, headers=auth_header)
        resp = await client.get("/api/teams/t2", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["slug"] == "t2"

    async def test_get_team_not_found(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/teams/nope", headers=auth_header)
        assert resp.status_code == 404


# ============================================================
# 8. 健康检查
# ============================================================

class TestHealth:
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
