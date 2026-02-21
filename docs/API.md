# Skills Hub API 文档

## 概述

Skills Hub 提供两类 API：

1. **管理 API** — 通过 JWT Token 认证，供 Web UI 和管理操作使用
2. **Plugin API** — 通过 API Key 认证，供 AI/CLI 工具使用

完整的交互式 API 文档请访问 `/docs`（Swagger UI）或 `/redoc`。

---

## 认证

### JWT 认证（管理 API）

```bash
# 登录获取 token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 响应
{"access_token": "eyJ...", "token_type": "bearer"}

# 使用 token
curl http://localhost:8000/api/skills \
  -H "Authorization: Bearer eyJ..."
```

### API Key 认证（Plugin API）

```bash
# 先通过管理 API 创建 API Key
curl -X POST http://localhost:8000/api/keys \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"name": "my-cli-key"}'

# 响应（key 仅返回一次）
{"id": "...", "name": "my-cli-key", "key": "skh_abc123...", ...}

# 使用 API Key 调用 Plugin API
curl http://localhost:8000/api/v1/skills/catalog \
  -H "Authorization: Bearer skh_abc123..."
```

---

## 管理 API

### 认证

#### POST /api/auth/register

注册新用户（可通过 `ALLOW_REGISTRATION=false` 关闭）。

```json
// 请求
{"username": "alice", "email": "alice@example.com", "password": "secret123"}

// 响应 201
{"id": "uuid", "username": "alice", "email": "alice@example.com", "role": "member", ...}
```

#### POST /api/auth/login

```json
// 请求
{"username": "alice", "password": "secret123"}

// 响应 200
{"access_token": "eyJ...", "token_type": "bearer"}
```

#### GET /api/auth/me

获取当前用户信息。需要 JWT。

---

### Skills

#### GET /api/skills

分页获取 Skills 列表。

| 参数 | 类型 | 说明 |
|---|---|---|
| q | string | 搜索关键词（名称/描述） |
| tag | string | 按标签筛选 |
| visibility | string | public/team/private |
| page | int | 页码，默认 1 |
| size | int | 每页数量，默认 20 |

```json
// 响应
{
  "items": [
    {
      "id": "uuid",
      "name": "deploy-k8s",
      "display_name": "K8s 部署",
      "description": "...",
      "tags": ["devops", "k8s"],
      "visibility": "public",
      "is_published": true,
      "latest_version": "1.2.0",
      ...
    }
  ],
  "total": 42
}
```

#### POST /api/skills

创建 Skill。名称必须是 kebab-case。

```json
// 请求
{
  "name": "deploy-k8s",
  "display_name": "K8s 部署指南",
  "description": "标准化 Kubernetes 部署流程",
  "tags": ["devops", "k8s"],
  "visibility": "public"
}
```

#### GET /api/skills/{name}

获取 Skill 详情。

#### PUT /api/skills/{name}

更新 Skill 元数据。

#### DELETE /api/skills/{name}

删除 Skill（需要是作者或 admin）。

---

### 版本管理

#### POST /api/skills/{name}/versions

发布新版本。

```json
// 请求
{
  "version": "1.2.0",
  "content": "---\ntitle: Deploy K8s\n---\n\n# K8s 部署指南\n\n...",
  "changelog": "添加了 HPA 自动扩缩配置",
  "files": {
    "references/hpa.yaml": "apiVersion: autoscaling/v2\n...",
    "examples/deployment.yaml": "apiVersion: apps/v1\n..."
  }
}
```

#### GET /api/skills/{name}/versions

获取版本列表。

#### GET /api/skills/{name}/versions/{ver}

获取特定版本详情（含附件文件）。

---

### API Keys

#### POST /api/keys

创建 API Key。

```json
// 请求
{"name": "production-key", "scopes": ["read"]}

// 响应（key 仅此一次返回）
{"id": "uuid", "name": "production-key", "key": "skh_...", "scopes": ["read"], ...}
```

#### GET /api/keys

列出当前用户的所有 API Keys。

#### DELETE /api/keys/{key_id}

删除 API Key。

---

### 团队

#### POST /api/teams

```json
{"name": "后端组", "slug": "backend-team", "description": "后端开发团队"}
```

#### GET /api/teams

列出所有团队。

---

## Plugin API

> 以下接口使用 API Key 认证（`Authorization: Bearer skh_...`）

### POST /api/v1/skills/resolve

批量获取 Skills 内容。**这是核心接口**，供 AI 和 CLI 使用。

```json
// 请求
{
  "skills": ["deploy-k8s", "code-review@1.0.0"]
}

// 响应
{
  "skills": [
    {
      "name": "deploy-k8s",
      "version": "1.2.0",
      "description": "标准化 K8s 部署流程",
      "content": "---\ntitle: Deploy K8s\n---\n\n# K8s 部署指南\n...",
      "files": {
        "references/hpa.yaml": "...",
        "examples/deployment.yaml": "..."
      }
    },
    {
      "name": "code-review",
      "version": "1.0.0",
      "description": "代码审查标准",
      "content": "...",
      "files": {}
    }
  ]
}
```

- 支持 `name@version` 语法指定版本
- 不指定版本时返回最新版本
- 未找到的 skill 会被静默跳过

### GET /api/v1/skills/catalog

列出所有已发布的公开 Skills。

```json
{
  "skills": [
    {"name": "deploy-k8s", "description": "...", "version": "1.2.0", "tags": ["devops"]},
    {"name": "code-review", "description": "...", "version": "1.0.0", "tags": ["quality"]}
  ]
}
```

### GET /api/v1/skills/{name}/raw

获取 Skill 的原始 SKILL.md 内容。

| 参数 | 类型 | 说明 |
|---|---|---|
| version | string | 可选，指定版本号 |

```json
{"name": "deploy-k8s", "version": "1.2.0", "content": "# K8s 部署指南\n..."}
```

> **注意**：Plugin API 仅返回 `visibility: "public"` 的 Skills。API Key 需包含 `read` scope。

---

## MCP Server

Skills Hub 提供标准 MCP（Model Context Protocol）SSE 端点，Claude Code 原生支持。

### 端点

```
SSE: http://localhost:8000/mcp
```

### 配置方式

在 `~/.claude.json` 中添加：

```json
{
  "mcpServers": {
    "skills-hub": {
      "type": "sse",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer skh_your_api_key"
      }
    }
  }
}
```

### 可用工具

MCP Server 暴露以下工具供 Claude Code 调用：

| 工具 | 说明 |
|---|---|
| `list_skills` | 列出所有已发布的公开 Skills |
| `get_skill` | 获取指定 Skill 的 SKILL.md 内容 |
| `resolve_skills` | 批量解析多个 Skills |
| `search_skills` | 按关键词搜索 Skills |

---

## 一键集成配置

### 配置脚本

项目根目录提供 `setup-claude.sh` 交互式脚本：

```bash
bash setup-claude.sh
```

自动完成：
1. 创建 `~/.claude/hooks/fetch-skills.sh`（Hook 脚本）
2. 更新 `~/.claude/settings.json` 添加 `UserPromptSubmit` Hook
3. 更新 `~/.claude.json` 添加 MCP Server 配置
4. 设置 `SKILLS_HUB_URL` 和 `SKILLS_HUB_API_KEY` 环境变量

### Web UI 集成指南

前端 `/setup` 页面提供图形化的配置向导，包含可复制的命令和逐步说明。
