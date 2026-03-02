# Skills Hub - 面向团队的私有 Skills 平台

<p align="center">
  <strong>统一管理、授权分发、可审计追踪的 Skills 基础设施</strong><br>
  面向 Claude Code / Codex 等代码智能平台的企业级 Skills Hub
</p>

## 平台定位

当团队把 Skills 当作工程资产来维护时，单纯的本地文件和零散仓库管理会很快遇到三个问题：

1. 资产分散：Skills 分布在个人机器和多个仓库，难发现、难复用。  
2. 边界不清：谁可以看、谁可以用、谁改过什么，缺少统一治理。  
3. 接入不稳：不同项目、不同平台接入方式不统一，难规模化推广。  

Skills Hub 作为“Skill 管理与分发控制面”，把上述问题收敛为统一平台能力。

## 平台特性（重点）

### 1) Skills 资产化管理

- **统一目录**：集中存储全部 Skills，支持名称/描述/标签检索。
- **版本化发布**：每次变更生成版本，支持 semver 和版本回溯。
- **在线编辑与文件管理**：支持 Web 端编辑 Skill 主体与附属文件。
- **附属文件下载**：支持直接下载 Skill 附件，便于本地复用与调试。

### 2) 访问控制与范围治理

- **订阅门禁（核心）**：只有“已订阅且启用”的 Skill 才会通过 Plugin API 返回。
- **可见性分级**：`public / team / private` 三层范围控制。
- **Team 范围隔离**：Team Skill 必须显式指定可见 Team，非目标 Team 用户不可见不可用。
- **API Key 认证**：通过 API Key 统一给 AI/CLI 接入，便于策略和审计。

### 3) 组织协作与可审计性

- **团队协作模型**：按 Team 管理可见范围和协作边界。
- **编辑记录追踪**：记录 Skill 与附属文件修改历史、修改人、修改时间。
- **单一超级管理员模型**：admin 可全局可见，便于平台治理和运维处理。

### 4) 多平台接入能力

- **Claude Code 一键接入**：`setup-claude.sh` 自动配置 Hook + MCP + 环境变量。
- **项目级配置**：每个项目可独立 `.skills-hub.json`，支持不同 URL / API Key / 默认 skills。
- **MCP 原生支持**：支持 SSE MCP Server 接入，兼容标准 MCP 客户端。
- **脚本化验证**：`scripts/claude/smoke-test.sh` 提供连通性与权限快速检查。

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

## 核心使用机制：订阅驱动分发

Skills Hub 的 Plugin API 不是“全量技能目录”，而是“当前用户已订阅技能目录”：

- `catalog` 只返回当前用户已订阅且启用的已发布 Skills
- `resolve` 只解析当前用户已订阅且启用的 Skills
- `raw` 对未订阅 Skill 返回 `403 Not subscribed to this skill`

推荐流程：

1. 创建并发布 Skill（作者会自动订阅该 Skill）
2. 在 Skills 页面按需订阅/取消订阅
3. 在设置页面创建 API Key
4. 使用 API Key 调用 Plugin API（`catalog / resolve / raw`）

## 已实现能力清单

- 用户认证（注册 / 登录 / JWT）
- Skill CRUD（创建 / 编辑 / 删除 / 查看）
- 版本管理（发布、回溯、semver）
- Plugin API（`resolve / catalog / raw`）
- API Key 管理（创建、查看、编辑、删除）
- 订阅机制（按订阅过滤可用 Skills）
- 团队管理（Team 创建与成员关系）
- 可见性控制（public / team / private）
- 在线编辑器（Markdown + 预览）
- 编辑记录（Skill 与附属文件）
- 附属文件下载
- MCP Server（SSE 协议）
- Claude Code 一键集成脚本
- Docker Compose 一键部署
- 输入校验与基础安全防护

## 规划中

- 使用统计
- 评分 / 评论
- Webhook 通知
- 审核流程
- 从 Git 仓库批量导入

## AI 集成

### 方式一：一键配置脚本（推荐）

项目提供了交互式和非交互式配置脚本，自动完成 Hook + MCP + 环境变量的配置。

#### 1) 交互式（本地手动配置）

```bash
cd skills-hub
bash setup-claude.sh
```

脚本会自动：
- 创建 `~/.claude/hooks/fetch-skills.sh`（用户提交提示时自动匹配 Skills）
- 更新 `~/.claude/settings.json` 添加 Hook 配置
- 更新 `~/.claude.json` 添加 MCP Server 配置
- 设置 `SKILLS_HUB_URL` 和 `SKILLS_HUB_API_KEY` 环境变量
- 可选写入当前项目 `.skills-hub.json`（项目级 URL / API Key / 默认 skills）

#### 2) 非交互式（一条命令，适合快速接入）

```bash
cd skills-hub
bash setup-claude.sh \
  --url http://127.0.0.1:8000 \
  --api-key skh_your_api_key \
  --project-dir /path/to/your/project \
  --write-project true \
  --non-interactive
```

也可以用封装脚本（自动调用 `setup-claude.sh`）：

```bash
cd skills-hub
bash scripts/claude/bootstrap.sh \
  --url http://127.0.0.1:8000 \
  --api-key skh_your_api_key \
  --project-dir /path/to/your/project \
  --skills deploy-k8s,code-review
```

配置完成后可执行连通性测试：

```bash
bash scripts/claude/smoke-test.sh --project-dir /path/to/your/project
```

### 项目级配置（推荐）

为了支持“不同项目使用不同 Skills Hub/Key”，可以在项目根目录创建 `.skills-hub.json`：

```json
{
  "url": "http://127.0.0.1:8000",
  "api_key": "skh_xxx",
  "skills": ["deploy-k8s", "code-review"]
}
```

Hook 会优先读取该文件；如果没有，再回退到环境变量 `SKILLS_HUB_URL` 和 `SKILLS_HUB_API_KEY`。

也可以在前端 Web UI 的 **集成指南** 页面（`/setup`）查看逐步配置说明和可复制的命令。

### 方式二：MCP Server

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

### 方式三：CLAUDE.md 声明

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

### 方式四：批量解析 API

```bash
curl -X POST https://skills.company.internal/api/v1/skills/resolve \
  -H "Authorization: Bearer skh_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"skills": ["deploy-k8s", "code-review@1.2.0"]}'
```

### 验证“仅订阅可用”的最小示例

```bash
# 1) 先获取 JWT（用于订阅操作）
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

# 2) 订阅某个 Skill（示例：deploy-k8s）
curl -X POST http://localhost:8000/api/skills/deploy-k8s/subscribe \
  -H "Authorization: Bearer $TOKEN"

# 3) 使用 API Key 查看目录（只会出现已订阅技能）
curl http://localhost:8000/api/v1/skills/catalog \
  -H "Authorization: Bearer skh_your_api_key"

# 4) 取消订阅后，再访问 raw 会返回 403
curl -X DELETE http://localhost:8000/api/skills/deploy-k8s/subscribe \
  -H "Authorization: Bearer $TOKEN"
curl http://localhost:8000/api/v1/skills/deploy-k8s/raw \
  -H "Authorization: Bearer skh_your_api_key"
```

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
| `/api/skills/{name}/subscribe` | POST/DELETE | 订阅/取消订阅 Skill | JWT |
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
├── scripts/
│   └── claude/
│       ├── bootstrap.sh        # Claude Code 非交互快速配置
│       └── smoke-test.sh       # Claude Code 集成连通性检查
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
