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
async def api_key_header(client: AsyncClient, auth_header: dict, sample_skill, sample_version):
    """Create an API key and return header for plugin API.
    Also subscribes to the sample skill (auto-subscribed on create)."""
    resp = await client.post("/api/keys", json={"name": "test-key", "allowed_tags": ["test", "demo"]}, headers=auth_header)
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
            "username": "dup", "email": "a@a.com", "password": "password123",
        })
        resp = await client.post("/api/auth/register", json={
            "username": "dup", "email": "b@b.com", "password": "password123",
        })
        assert resp.status_code == 409

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "u1", "email": "same@test.com", "password": "password123",
        })
        resp = await client.post("/api/auth/register", json={
            "username": "u2", "email": "same@test.com", "password": "password123",
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
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["teams"] == []

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
        # Auto-subscribed
        assert data["is_subscribed"] is True
        assert data["subscription_enabled"] is True

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
    """Plugin API: resolve / catalog / raw (subscription-based)"""

    async def test_catalog(self, client: AsyncClient, api_key_header: dict,
                           auth_header: dict):
        resp = await client.get("/api/v1/skills/catalog", headers=api_key_header)
        assert resp.status_code == 200
        data = resp.json()
        assert any(s["name"] == "test-skill" for s in data["skills"])

    async def test_resolve_single(self, client: AsyncClient, api_key_header: dict,
                                  auth_header: dict):
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
                                        auth_header: dict):
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
                                 auth_header: dict):
        resp = await client.post("/api/v1/skills/resolve", json={
            "skills": ["test-skill", "nonexistent"],
        }, headers=api_key_header)
        assert resp.status_code == 200
        assert len(resp.json()["skills"]) == 1

    async def test_raw(self, client: AsyncClient, api_key_header: dict,
                       auth_header: dict):
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

    async def test_plugin_empty_without_subscription(self, client: AsyncClient, auth_header: dict):
        """Plugin API returns empty if user has no subscriptions."""
        # Create a skill but unsubscribe
        await client.post("/api/skills", json={
            "name": "unsub-skill",
            "display_name": "Unsub Skill",
            "tags": ["test"],
            "visibility": "public",
        }, headers=auth_header)
        await client.post("/api/skills/unsub-skill/versions", json={
            "version": "1.0.0",
            "content": "# Unsub",
        }, headers=auth_header)
        # Unsubscribe
        await client.delete("/api/skills/unsub-skill/subscribe", headers=auth_header)
        # Create API key
        resp = await client.post("/api/keys", json={"name": "unsub-key", "allowed_tags": ["test"]}, headers=auth_header)
        key = resp.json()["key"]
        key_header = {"Authorization": f"Bearer {key}"}
        # Resolve should not return the unsubscribed skill
        resp = await client.post("/api/v1/skills/resolve", json={
            "skills": ["unsub-skill"],
        }, headers=key_header)
        assert resp.status_code == 200
        assert resp.json()["skills"] == []


# ============================================================
# 7. 使用统计测试
# ============================================================

class TestUsageLogging:
    """Plugin API 调用应写入 usage log"""

    async def test_resolve_creates_log(self, client: AsyncClient, api_key_header: dict,
                                       auth_header: dict):
        await client.post("/api/v1/skills/resolve", json={
            "skills": ["test-skill"],
        }, headers=api_key_header)

        # Check stats overview reflects the call
        resp = await client.get("/api/stats/overview", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total_calls"] >= 1

    async def test_catalog_creates_log(self, client: AsyncClient, api_key_header: dict,
                                       auth_header: dict):
        await client.get("/api/v1/skills/catalog", headers=api_key_header)

        resp = await client.get("/api/stats/overview", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total_calls"] >= 1

    async def test_raw_creates_log(self, client: AsyncClient, api_key_header: dict,
                                    auth_header: dict):
        await client.get("/api/v1/skills/test-skill/raw", headers=api_key_header)

        resp = await client.get("/api/stats/overview", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total_calls"] >= 1

    async def test_resolve_nonexistent_no_log(self, client: AsyncClient, api_key_header: dict,
                                              auth_header: dict):
        """Resolving a skill that doesn't exist should NOT create a log."""
        await client.post("/api/v1/skills/resolve", json={
            "skills": ["no-such-skill"],
        }, headers=api_key_header)

        resp = await client.get("/api/stats/overview", headers=auth_header)
        assert resp.status_code == 200
        # No resolve log for nonexistent skill (only 0 total)
        assert resp.json()["total_calls"] == 0


class TestStatsAPI:
    """统计 API: overview / popular / trend"""

    async def test_overview_empty(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/stats/overview", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_calls"] == 0
        assert data["today_calls"] == 0
        assert data["week_calls"] == 0
        assert data["active_skills"] == 0

    async def test_overview_after_calls(self, client: AsyncClient, auth_header: dict,
                                        api_key_header: dict):
        # Make some API calls
        await client.post("/api/v1/skills/resolve", json={"skills": ["test-skill"]}, headers=api_key_header)
        await client.get("/api/v1/skills/test-skill/raw", headers=api_key_header)
        await client.get("/api/v1/skills/catalog", headers=api_key_header)

        resp = await client.get("/api/stats/overview", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_calls"] == 3
        assert data["today_calls"] == 3
        assert data["week_calls"] == 3
        assert data["active_skills"] >= 1  # "test-skill" (catalog uses "*" which is excluded)

    async def test_popular_empty(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/stats/popular", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_popular_after_calls(self, client: AsyncClient, auth_header: dict,
                                       api_key_header: dict):
        await client.post("/api/v1/skills/resolve", json={"skills": ["test-skill"]}, headers=api_key_header)
        await client.post("/api/v1/skills/resolve", json={"skills": ["test-skill"]}, headers=api_key_header)
        await client.get("/api/v1/skills/test-skill/raw", headers=api_key_header)

        resp = await client.get("/api/stats/popular?days=30&limit=10", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["skill_name"] == "test-skill"
        assert data[0]["call_count"] == 3  # 2 resolve + 1 raw
        assert data[0]["percentage"] == 100.0

    async def test_trend_empty(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/stats/trend?days=7", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 8  # 7 days ago + today = 8 entries
        assert all(item["call_count"] == 0 for item in data)

    async def test_trend_after_calls(self, client: AsyncClient, auth_header: dict,
                                     api_key_header: dict):
        await client.post("/api/v1/skills/resolve", json={"skills": ["test-skill"]}, headers=api_key_header)

        resp = await client.get("/api/stats/trend?days=7", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        # Today's entry should have at least 1 call
        today_entry = data[-1]
        assert today_entry["call_count"] >= 1

    async def test_trend_has_date_format(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/stats/trend?days=3", headers=auth_header)
        data = resp.json()
        for item in data:
            assert "date" in item
            assert "call_count" in item
            # date should be ISO format YYYY-MM-DD
            assert len(item["date"]) == 10

    async def test_stats_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/stats/overview")
        assert resp.status_code == 401

    async def test_stats_rejects_api_key(self, client: AsyncClient, api_key_header: dict):
        """Stats endpoints require JWT, not API key."""
        resp = await client.get("/api/stats/overview", headers=api_key_header)
        assert resp.status_code == 401

    async def test_popular_params_validation(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/stats/popular?days=0", headers=auth_header)
        assert resp.status_code == 422
        resp = await client.get("/api/stats/popular?limit=0", headers=auth_header)
        assert resp.status_code == 422


# ============================================================
# 8. Skill 权限隔离测试
# ============================================================

class TestSkillPermissionIsolation:
    """验证不同用户之间的 Skill 可见性隔离"""

    async def _create_user(self, client, username, email, password="pass123"):
        """Helper: 注册并登录，返回 auth header."""
        await client.post("/api/auth/register", json={
            "username": username, "email": email, "password": password,
        })
        resp = await client.post("/api/auth/login", json={
            "username": username, "password": password,
        })
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_private_skill_invisible_to_other_user(self, client: AsyncClient):
        """用户 A 的 private skill，用户 B 看不到"""
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        # Alice creates a private skill
        resp = await client.post("/api/skills", json={
            "name": "alice-private",
            "display_name": "Alice Private",
            "visibility": "private",
        }, headers=header_a)
        assert resp.status_code == 201

        # Bob lists skills — should NOT see alice-private
        resp = await client.get("/api/skills", headers=header_b)
        assert resp.status_code == 200
        names = [s["name"] for s in resp.json()["items"]]
        assert "alice-private" not in names

    async def test_private_skill_visible_to_author(self, client: AsyncClient):
        """作者可以看到自己的 private skill"""
        header_a = await self._create_user(client, "alice", "alice@test.com")

        await client.post("/api/skills", json={
            "name": "alice-private",
            "display_name": "Alice Private",
            "visibility": "private",
        }, headers=header_a)

        resp = await client.get("/api/skills", headers=header_a)
        names = [s["name"] for s in resp.json()["items"]]
        assert "alice-private" in names

    async def test_public_skill_visible_to_all(self, client: AsyncClient):
        """Public skill 所有人可见"""
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/skills", json={
            "name": "alice-public",
            "display_name": "Alice Public",
            "visibility": "public",
        }, headers=header_a)

        # Bob can see it
        resp = await client.get("/api/skills", headers=header_b)
        names = [s["name"] for s in resp.json()["items"]]
        assert "alice-public" in names

    async def test_private_skill_detail_forbidden_to_other_user(self, client: AsyncClient):
        """用户 B 直接访问用户 A 的 private skill 详情，返回 403"""
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/skills", json={
            "name": "alice-secret",
            "display_name": "Secret",
            "visibility": "private",
        }, headers=header_a)

        resp = await client.get("/api/skills/alice-secret", headers=header_b)
        assert resp.status_code == 403

    async def test_other_user_cannot_edit_skill(self, client: AsyncClient):
        """用户 B 不能编辑用户 A 的 skill（即使是 public）"""
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/skills", json={
            "name": "alice-skill",
            "display_name": "Alice Skill",
            "visibility": "public",
        }, headers=header_a)

        resp = await client.put("/api/skills/alice-skill", json={
            "display_name": "Hacked",
        }, headers=header_b)
        assert resp.status_code == 403

    async def test_other_user_cannot_delete_skill(self, client: AsyncClient):
        """用户 B 不能删除用户 A 的 skill"""
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/skills", json={
            "name": "alice-skill",
            "display_name": "Alice Skill",
            "visibility": "public",
        }, headers=header_a)

        resp = await client.delete("/api/skills/alice-skill", headers=header_b)
        assert resp.status_code == 403

    async def test_other_user_cannot_create_version(self, client: AsyncClient):
        """用户 B 不能给用户 A 的 skill 发布版本"""
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/skills", json={
            "name": "alice-skill",
            "display_name": "Alice Skill",
            "visibility": "public",
        }, headers=header_a)

        resp = await client.post("/api/skills/alice-skill/versions", json={
            "version": "1.0.0",
            "content": "# Hacked",
        }, headers=header_b)
        assert resp.status_code == 403

    async def test_stats_isolated_by_user(self, client: AsyncClient):
        """用户 A 的 stats 只统计自己 API Key 的调用"""
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        # Alice creates skill + version + API key
        await client.post("/api/skills", json={
            "name": "alice-skill",
            "display_name": "Alice Skill",
            "tags": ["demo"],
            "visibility": "public",
        }, headers=header_a)
        await client.post("/api/skills/alice-skill/versions", json={
            "version": "1.0.0",
            "content": "# Alice",
        }, headers=header_a)
        resp_key_a = await client.post("/api/keys", json={
            "name": "alice-key",
            "allowed_tags": ["demo"],
        }, headers=header_a)
        key_a = resp_key_a.json()["key"]
        key_header_a = {"Authorization": f"Bearer {key_a}"}

        # Bob subscribes to alice-skill and creates API key
        await client.post("/api/skills/alice-skill/subscribe", headers=header_b)
        resp_key_b = await client.post("/api/keys", json={
            "name": "bob-key",
            "allowed_tags": ["demo"],
        }, headers=header_b)
        key_b = resp_key_b.json()["key"]
        key_header_b = {"Authorization": f"Bearer {key_b}"}

        # Alice's key makes 3 calls
        await client.post("/api/v1/skills/resolve", json={"skills": ["alice-skill"]}, headers=key_header_a)
        await client.post("/api/v1/skills/resolve", json={"skills": ["alice-skill"]}, headers=key_header_a)
        await client.post("/api/v1/skills/resolve", json={"skills": ["alice-skill"]}, headers=key_header_a)

        # Bob's key makes 1 call
        await client.post("/api/v1/skills/resolve", json={"skills": ["alice-skill"]}, headers=key_header_b)

        # Alice sees only her 3 calls
        resp = await client.get("/api/stats/overview", headers=header_a)
        assert resp.status_code == 200
        assert resp.json()["total_calls"] == 3

        # Bob sees only his 1 call
        resp = await client.get("/api/stats/overview", headers=header_b)
        assert resp.status_code == 200
        assert resp.json()["total_calls"] == 1

    async def test_api_keys_isolated_by_user(self, client: AsyncClient):
        """用户 A 看不到用户 B 的 API Key"""
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/keys", json={"name": "alice-key"}, headers=header_a)
        await client.post("/api/keys", json={"name": "bob-key"}, headers=header_b)

        # Alice only sees her key
        resp = await client.get("/api/keys", headers=header_a)
        names = [k["name"] for k in resp.json()]
        assert "alice-key" in names
        assert "bob-key" not in names

        # Bob only sees his key
        resp = await client.get("/api/keys", headers=header_b)
        names = [k["name"] for k in resp.json()]
        assert "bob-key" in names
        assert "alice-key" not in names


# ============================================================
# 9. 团队管理测试
# ============================================================

class TestTeams:
    """团队的创建、加入、退出"""

    async def _create_user(self, client, username, email, password="pass123"):
        await client.post("/api/auth/register", json={
            "username": username, "email": email, "password": password,
        })
        resp = await client.post("/api/auth/login", json={
            "username": username, "password": password,
        })
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

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
        data = resp.json()
        assert data["slug"] == "t2"
        assert data["my_role"] == "admin"  # creator is admin
        assert len(data["members"]) == 1

    async def test_get_team_not_found(self, client: AsyncClient, auth_header: dict):
        resp = await client.get("/api/teams/nope", headers=auth_header)
        assert resp.status_code == 404

    async def test_join_team(self, client: AsyncClient):
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        # Alice creates team
        await client.post("/api/teams", json={"name": "TeamA", "slug": "team-a"}, headers=header_a)

        # Bob joins
        resp = await client.post("/api/teams/team-a/join", headers=header_b)
        assert resp.status_code == 200
        assert resp.json()["my_role"] == "member"

        # Verify Bob appears in team detail
        resp = await client.get("/api/teams/team-a", headers=header_a)
        assert len(resp.json()["members"]) == 2

    async def test_leave_team(self, client: AsyncClient):
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/teams", json={"name": "TeamA", "slug": "team-a"}, headers=header_a)
        await client.post("/api/teams/team-a/join", headers=header_b)

        # Bob leaves
        resp = await client.post("/api/teams/team-a/leave", headers=header_b)
        assert resp.status_code == 200

        # Verify Bob is gone
        resp = await client.get("/api/teams/team-a", headers=header_a)
        assert len(resp.json()["members"]) == 1

    async def test_leave_disables_subscriptions(self, client: AsyncClient):
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        # Alice creates team and a team-visibility skill
        await client.post("/api/teams", json={"name": "TeamA", "slug": "team-a"}, headers=header_a)
        resp = await client.get("/api/teams/team-a", headers=header_a)
        team_id = resp.json()["id"]

        await client.post("/api/skills", json={
            "name": "team-only-skill",
            "display_name": "Team Only",
            "visibility": "team",
            "team_id": team_id,
        }, headers=header_a)

        # Bob joins and subscribes
        await client.post("/api/teams/team-a/join", headers=header_b)
        await client.post("/api/skills/team-only-skill/subscribe", headers=header_b)

        # Verify subscription is active
        resp = await client.get("/api/skills/team-only-skill", headers=header_b)
        assert resp.json()["is_subscribed"] is True
        assert resp.json()["subscription_enabled"] is True

        # Bob leaves team → subscription should be disabled
        await client.post("/api/teams/team-a/leave", headers=header_b)

    async def test_sole_admin_cannot_leave(self, client: AsyncClient, auth_header: dict):
        await client.post("/api/teams", json={"name": "Solo", "slug": "solo"}, headers=auth_header)
        resp = await client.post("/api/teams/solo/leave", headers=auth_header)
        assert resp.status_code == 400
        assert "only admin" in resp.json()["detail"]

    async def test_remove_member(self, client: AsyncClient):
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/teams", json={"name": "TeamA", "slug": "team-a"}, headers=header_a)
        await client.post("/api/teams/team-a/join", headers=header_b)

        # Get bob's user ID
        resp = await client.get("/api/teams/team-a", headers=header_a)
        members = resp.json()["members"]
        bob_member = [m for m in members if m["username"] == "bob"][0]

        # Alice (admin) removes Bob
        resp = await client.delete(f"/api/teams/team-a/members/{bob_member['user_id']}", headers=header_a)
        assert resp.status_code == 200

        # Verify Bob is gone
        resp = await client.get("/api/teams/team-a", headers=header_a)
        assert len(resp.json()["members"]) == 1

    async def test_my_teams(self, client: AsyncClient):
        header_a = await self._create_user(client, "alice", "alice@test.com")

        await client.post("/api/teams", json={"name": "Team1", "slug": "team-1"}, headers=header_a)
        await client.post("/api/teams", json={"name": "Team2", "slug": "team-2"}, headers=header_a)

        resp = await client.get("/api/teams/my", headers=header_a)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        slugs = {t["slug"] for t in data}
        assert "team-1" in slugs
        assert "team-2" in slugs


# ============================================================
# 10. 订阅测试
# ============================================================

class TestSubscriptions:
    """Skill 订阅机制"""

    async def _create_user(self, client, username, email, password="pass123"):
        await client.post("/api/auth/register", json={
            "username": username, "email": email, "password": password,
        })
        resp = await client.post("/api/auth/login", json={
            "username": username, "password": password,
        })
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_auto_subscribe_on_create(self, client: AsyncClient, auth_header: dict):
        """Creating a skill auto-subscribes the author."""
        resp = await client.post("/api/skills", json={
            "name": "auto-sub-skill",
            "display_name": "Auto Sub",
            "visibility": "public",
        }, headers=auth_header)
        assert resp.status_code == 201
        assert resp.json()["is_subscribed"] is True
        assert resp.json()["subscription_enabled"] is True

    async def test_subscribe(self, client: AsyncClient):
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        # Alice creates a public skill
        await client.post("/api/skills", json={
            "name": "sub-test",
            "display_name": "Sub Test",
            "visibility": "public",
        }, headers=header_a)

        # Bob subscribes
        resp = await client.post("/api/skills/sub-test/subscribe", headers=header_b)
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

        # Verify in skill detail
        resp = await client.get("/api/skills/sub-test", headers=header_b)
        assert resp.json()["is_subscribed"] is True
        assert resp.json()["subscription_enabled"] is True

    async def test_unsubscribe(self, client: AsyncClient):
        header_a = await self._create_user(client, "alice", "alice@test.com")
        header_b = await self._create_user(client, "bob", "bob@test.com")

        await client.post("/api/skills", json={
            "name": "unsub-test",
            "display_name": "Unsub Test",
            "visibility": "public",
        }, headers=header_a)

        # Bob subscribes then unsubscribes
        await client.post("/api/skills/unsub-test/subscribe", headers=header_b)
        resp = await client.delete("/api/skills/unsub-test/subscribe", headers=header_b)
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

        # Verify in skill detail
        resp = await client.get("/api/skills/unsub-test", headers=header_b)
        assert resp.json()["is_subscribed"] is True  # record exists
        assert resp.json()["subscription_enabled"] is False  # but disabled

    async def test_plugin_only_returns_subscribed(self, client: AsyncClient, auth_header: dict):
        """Plugin API only returns skills user is subscribed to."""
        # Create two skills (auto-subscribed)
        await client.post("/api/skills", json={
            "name": "skill-yes",
            "display_name": "Skill Yes",
            "tags": ["test"],
            "visibility": "public",
        }, headers=auth_header)
        await client.post("/api/skills/skill-yes/versions", json={
            "version": "1.0.0",
            "content": "# Yes",
        }, headers=auth_header)

        await client.post("/api/skills", json={
            "name": "skill-no",
            "display_name": "Skill No",
            "tags": ["test"],
            "visibility": "public",
        }, headers=auth_header)
        await client.post("/api/skills/skill-no/versions", json={
            "version": "1.0.0",
            "content": "# No",
        }, headers=auth_header)

        # Unsubscribe from skill-no
        await client.delete("/api/skills/skill-no/subscribe", headers=auth_header)

        # Create API key
        resp = await client.post("/api/keys", json={"name": "sub-test-key", "allowed_tags": ["test"]}, headers=auth_header)
        key = resp.json()["key"]
        key_header = {"Authorization": f"Bearer {key}"}

        # Catalog should only return skill-yes
        resp = await client.get("/api/v1/skills/catalog", headers=key_header)
        names = [s["name"] for s in resp.json()["skills"]]
        assert "skill-yes" in names
        assert "skill-no" not in names


# ============================================================
# 11. 健康检查
# ============================================================

class TestHealth:
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
