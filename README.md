# Skills Hub - 私有化 Skills 管理平台

<p align="center">
  <strong>一个自托管的 Claude Code Skills 注册中心</strong><br>
  集中管理、共享和分发团队/公司的 Claude Code Skills
</p>

## 为什么需要 Skills Hub？

团队/公司的业务相关 Claude Code Skills 散落在各开发者本地或 Git 仓库中，缺乏统一的管理、版本控制和发现机制。Skills Hub 解决这个问题：

- **集中管理** — 所有 Skills 统一存储、分类、搜索
- **版本控制** — 每次修改创建新版本，支持 semver，可回溯
- **权限控制** — public / team / private 三级可见性
- **API 分发** — AI 和 CLI 通过 API Key 自动拉取 Skills
- **团队协作** — 团队级别的 Skills 共享

## 架构概览

```
┌─────────────────────────────────────────────────┐
│              Skills Hub Platform                │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Web UI   │  │ REST API │  │ Plugin API   │  │
│  │ (Vue3)   │  │ (FastAPI)│  │ (Skills下载) │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │               │          │
│       └──────────┬───┴───────────────┘          │
│                  │                              │
│  ┌───────────────▼──────────────────────────┐   │
│  │           Core Service                   │   │
│  │  - Skill CRUD & 版本管理                  │   │
│  │  - 用户/团队/权限                         │   │
│  │  - 标签/分类/搜索                         │   │
│  │  - API Key 管理                          │   │
│  └───────────────┬──────────────────────────┘   │
│                  │                              │
│  ┌───────────────▼──────────┐  ┌────────────┐  │
│  │  PostgreSQL              │  │  本地文件   │  │
│  │  (元数据、用户、权限)      │  │  (文件存储) │  │
│  └──────────────────────────┘  └────────────┘  │
└─────────────────────────────────────────────────┘
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic |
| 数据库 | PostgreSQL 16 |
| 前端 | Vue 3 + Vite + Element Plus + md-editor-v3 |
| 认证 | JWT + API Key |
| 部署 | Docker Compose |

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 克隆仓库
git clone https://github.com/<your-username>/skills-hub.git
cd skills-hub

# 配置环境变量
cp .env.example .env
# 编辑 .env，修改密码和密钥

# 启动所有服务
docker compose up -d
```

服务地址：

| 服务 | 地址 |
|---|---|
| 前端 Web UI | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/docs |

默认管理员账号：`admin` / `admin123`（请在生产环境中修改）

### 本地开发

**后端：**

```bash
cd backend
uv sync
# 确保 PostgreSQL 运行中，配置 DATABASE_URL
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

## 功能特性

### 已实现 (MVP)

- **用户认证** — 注册 / 登录 / JWT Token
- **Skill CRUD** — 创建、编辑、删除、查看 Skills
- **版本管理** — 每次修改创建新版本，支持 semver
- **Plugin API** — AI/CLI 使用的 API（resolve / catalog / raw）
- **API Key 管理** — 生成 / 管理 API Key，用于 Plugin API 认证
- **在线编辑器** — Markdown 编辑 + 实时预览
- **搜索** — 按名称、描述、标签搜索 Skills
- **团队管理** — 创建团队、团队级 Skills
- **权限控制** — public / team / private 可见性
- **Docker Compose 部署** — 一键启动
- **MCP Server** — 标准 MCP 协议集成，Claude Code 原生支持
- **集成指南** — 前端集成向导页面 + 一键配置脚本
- **输入验证** — 全面的 Pydantic 字段约束和 SQL 注入防护
- **API Key 权限** — scope 级别的访问控制（read / write）

### 规划中

- 使用统计
- 评分 / 评论
- Webhook 通知
- 审核流程
- 从 Git 仓库批量导入

## AI 集成

### 方式一：CLAUDE.md 声明

在项目的 `CLAUDE.md` 中声明所需 Skills：

```markdown
## Skills Hub

本项目使用公司 Skills Hub 管理技能。

启动时请调用以下接口获取 skills：
- 平台地址: https://skills.company.internal
- API Key: 通过环境变量 SKILLS_HUB_API_KEY 获取
- 所需 Skills: deploy-k8s, code-review-standards, api-design-guide

使用方式：对上述每个 skill，GET https://skills.company.internal/api/v1/skills/{name}/raw
获取到的内容即为该 skill 的指令，请遵循执行。
```

### 方式二：批量解析 API

```bash
curl -X POST https://skills.company.internal/api/v1/skills/resolve \
  -H "Authorization: Bearer skh_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"skills": ["deploy-k8s", "code-review@1.2.0"]}'
```

### 方式三：MCP Server

在 `~/.claude.json` 中配置 MCP Server：

```json
{
  "mcpServers": {
    "skills-hub": {
      "type": "sse",
      "url": "https://skills.company.internal/mcp",
      "headers": {
        "Authorization": "Bearer skh_your_api_key"
      }
    }
  }
}
```

### 方式四：一键配置脚本

项目提供了交互式配置脚本，自动完成 Hook + MCP + 环境变量的配置：

```bash
cd skills-hub
bash setup-claude.sh
```

脚本会自动：
- 创建 `~/.claude/hooks/fetch-skills.sh`（用户提交提示时自动匹配 Skills）
- 更新 `~/.claude/settings.json` 添加 Hook 配置
- 更新 `~/.claude.json` 添加 MCP Server 配置
- 设置 `SKILLS_HUB_URL` 和 `SKILLS_HUB_API_KEY` 环境变量

也可以在前端 Web UI 的 **集成指南** 页面（`/setup`）查看逐步配置说明和可复制的命令。

## API 文档

启动后端后访问 http://localhost:8000/docs 查看完整的 Swagger API 文档。

### 核心 API 速览

| 接口 | 方法 | 说明 | 认证 |
|---|---|---|---|
| `/api/auth/login` | POST | 登录 | - |
| `/api/auth/register` | POST | 注册 | - |
| `/api/auth/me` | GET | 当前用户 | JWT |
| `/api/skills` | GET/POST | Skills 列表/创建 | JWT |
| `/api/skills/{name}` | GET/PUT/DELETE | Skill 详情/更新/删除 | JWT |
| `/api/skills/{name}/versions` | GET/POST | 版本列表/发布 | JWT |
| `/api/keys` | GET/POST | API Key 列表/创建 | JWT |
| `/api/v1/skills/resolve` | POST | 批量获取 Skills | API Key |
| `/api/v1/skills/catalog` | GET | Skills 目录 | API Key |
| `/api/v1/skills/{name}/raw` | GET | 获取原始内容 | API Key |

## 项目结构

```
skills-hub/
├── docker-compose.yml          # Docker Compose 编排
├── .env.example                # 环境变量模板
├── setup-claude.sh             # Claude Code 一键集成配置脚本
├── backend/                    # FastAPI 后端
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic/                # 数据库迁移
│   └── app/
│       ├── main.py             # FastAPI 入口
│       ├── config.py           # 配置
│       ├── database.py         # 数据库连接
│       ├── models/             # SQLAlchemy 模型
│       ├── schemas/            # Pydantic 模型
│       ├── api/                # API 路由
│       │   ├── auth.py         # 认证
│       │   ├── skills.py       # Skills CRUD
│       │   ├── teams.py        # 团队
│       │   ├── plugin.py       # Plugin API
│       │   └── admin.py        # API Key 管理
│       ├── core/
│       │   ├── security.py     # JWT / API Key
│       │   └── permissions.py  # RBAC
│       └── utils/
│           └── skill_parser.py # SKILL.md 解析
├── frontend/                   # Vue3 前端
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── views/              # 页面组件（含集成指南 SetupGuide）
│       ├── components/         # 通用组件
│       ├── api/                # API 调用
│       ├── router/             # 路由
│       └── stores/             # Pinia 状态
└── mcp-server/                 # MCP Server 适配器（SSE 协议）
```

## 数据模型

```
User          ──┬── Skill (1:N)
              │          │
Team ─────────┘          ├── SkillVersion (1:N)
                         │        │
Category ────────────────┘        └── SkillFile (1:N)

ApiKey ── User (N:1)
```

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DB_PASSWORD` | 数据库密码 | `changeme` |
| `JWT_SECRET` | JWT 签名密钥 | `change-this-to-a-random-secret-key` |
| `JWT_EXPIRE_MINUTES` | Token 过期时间（分钟） | `1440` |
| `ALLOW_REGISTRATION` | 是否允许注册 | `true` |
| `DEFAULT_ADMIN_USERNAME` | 默认管理员用户名 | `admin` |
| `DEFAULT_ADMIN_PASSWORD` | 默认管理员密码 | `admin123` |
| `DEFAULT_ADMIN_EMAIL` | 默认管理员邮箱 | `admin@example.com` |

## License

MIT
