# Skills Hub 实施计划

## 项目背景

团队/公司需要将业务相关的 Claude Code Skills 集中管理、共享和分发。目前 Skills 散落在各开发者本地或 Git 仓库中，缺乏统一的管理、版本控制和发现机制。

**目标**：构建一个自托管的 Skills 注册中心，开发者告诉 AI 平台地址 + skills 列表，AI 自动拉取并使用。

## 开发者工作流

```
┌───────────────┐     ┌──────────────┐     ┌──────────────────┐
│ .claude/       │     │ skills-hub   │     │ Claude Code      │
│ skills.json   │────▶│ CLI/API      │────▶│ 自动加载 Skills   │
│ (平台地址+列表)│     │ 拉取 SKILL.md│     │ 进入上下文        │
└───────────────┘     └──────────────┘     └──────────────────┘
```

## 实施阶段

### Phase 1: 项目初始化 + 后端核心 ✅

| # | 任务 | 状态 |
|---|------|------|
| 1 | 项目脚手架：pyproject.toml、FastAPI 入口、Docker Compose | ✅ 完成 |
| 2 | 数据库模型 + Alembic 迁移配置 | ✅ 完成 |
| 3 | 用户认证（JWT + API Key） | ✅ 完成 |
| 4 | Skill CRUD API | ✅ 完成 |
| 5 | SKILL.md 解析器（frontmatter + markdown） | ✅ 完成 |
| 6 | 版本管理（semver、版本列表、附件文件） | ✅ 完成 |

**数据模型设计：**

```
User:
  id, username, email, password_hash, role(admin/member),
  team_id, created_at

Team:
  id, name, slug, description, created_at

Skill:
  id, name(kebab-case), display_name, description,
  category_id, tags[], team_id, author_id,
  visibility(public/team/private),
  is_published, created_at, updated_at

SkillVersion:
  id, skill_id, version(semver),
  content(SKILL.md全文), metadata_json(JSON),
  changelog, created_at, published_at

SkillFile:
  id, skill_version_id, path, content, file_type

ApiKey:
  id, user_id, key_hash, name, scopes[],
  expires_at, created_at

Category:
  id, name, slug, parent_id, description
```

### Phase 2: Plugin API + API Key ✅

| # | 任务 | 状态 |
|---|------|------|
| 7 | API Key 生成 / 验证 | ✅ 完成 |
| 8 | Plugin API（resolve / catalog / raw） | ✅ 完成 |
| 9 | 接口测试 | ✅ 完成 |

**Plugin API 设计：**

```
POST /api/v1/skills/resolve    — 批量获取 skills（支持 "name@version" 语法）
GET  /api/v1/skills/catalog    — 列出所有已发布 skills
GET  /api/v1/skills/{name}/raw — 获取原始 SKILL.md 内容
```

### Phase 3: 前端 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10 | Vue3 项目搭建 + Element Plus | ✅ 完成 |
| 11 | 登录 / 注册页 | ✅ 完成 |
| 12 | Skills 列表 + 搜索 + 筛选 | ✅ 完成 |
| 13 | Skill 详情 + 版本历史 | ✅ 完成 |
| 14 | Markdown 编辑器（md-editor-v3） | ✅ 完成 |
| 15 | API Key 管理页 | ✅ 完成 |
| 16 | 团队管理页 | ✅ 完成 |
| 17 | Dashboard 概览页 | ✅ 完成 |

### Phase 4: 部署完善 ✅

| # | 任务 | 状态 |
|---|------|------|
| 18 | Docker Compose 编排（PostgreSQL + Backend + Frontend） | ✅ 完成 |
| 19 | Backend Dockerfile（uv 构建） | ✅ 完成 |
| 20 | Frontend Dockerfile（Vite 构建 + Nginx） | ✅ 完成 |
| 21 | Nginx 反向代理配置 | ✅ 完成 |
| 22 | 文档（README + API 文档自动生成 via FastAPI /docs） | ✅ 完成 |

### Phase 5: MCP Server + 集成向导 + 安全加固 ✅

| # | 任务 | 状态 |
|---|------|------|
| 23 | MCP Server 适配器（SSE 协议） | ✅ 完成 |
| 24 | 集成指南页面（SetupGuide.vue，步骤条 + 可复制命令） | ✅ 完成 |
| 25 | 一键配置脚本（setup-claude.sh，Hook + MCP + 环境变量） | ✅ 完成 |
| 26 | 输入验证加固（Pydantic Field 约束、SQL LIKE 转义） | ✅ 完成 |
| 27 | API Key scope 检查（Plugin API 强制 read 权限） | ✅ 完成 |
| 28 | 重复资源冲突处理（skill name / version 唯一约束 + 409） | ✅ 完成 |
| 29 | 前端修复（路由响应式、加载状态、剪贴板错误处理） | ✅ 完成 |

## 关键技术决策

### 1. 自动建表 vs Alembic 迁移

MVP 阶段使用 `Base.metadata.create_all()` 自动建表，同时保留 Alembic 配置供生产环境使用。

### 2. API Key 安全

- API Key 格式：`skh_` 前缀 + 32 字节 URL-safe token
- 存储时只保存 SHA-256 哈希，原始 key 仅在创建时返回一次
- 支持过期时间和 scopes 权限控制

### 3. 前端路由守卫

使用 Pinia store 管理 token，Vue Router `beforeEach` 守卫检查认证状态，未认证自动跳转登录页。

### 4. CORS 配置

开发阶段允许所有源（`allow_origins=["*"]`），生产环境应限制为实际前端域名。

## 未来规划

### P1（增强）
- 团队邀请成员机制
- 多级分类体系
- Skill 导入/导出（Git 仓库批量导入，导出为 zip）

### P2（进阶）
- 使用统计（拉取频率、热门 Skills）
- 评分 / 评论系统
- Webhook 通知（Slack / 飞书）
- 审核流程（发布需审批）

## 验证方式

1. `docker compose up` 启动全部服务
2. 通过 Web UI 注册用户、创建 Skill、发布版本
3. 生成 API Key
4. 用 curl 调用 Plugin API 验证：
   ```bash
   # 获取 catalog
   curl -H "Authorization: Bearer skh_xxx" http://localhost:8000/api/v1/skills/catalog

   # 批量解析
   curl -X POST http://localhost:8000/api/v1/skills/resolve \
     -H "Authorization: Bearer skh_xxx" \
     -H "Content-Type: application/json" \
     -d '{"skills": ["my-skill"]}'
   ```
5. 在 CLAUDE.md 中配置平台地址，验证 AI 能获取和使用 Skills
