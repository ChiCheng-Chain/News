# 打破信息茧房 · 开发进度交接文档

**最后更新：** 2026-03-26
**当前状态：** 后端已完成，前端待实现

---

## 一、项目整体目标

构建一个前后端系统，通过多 Agent 协同，每天生成精炼、多元视角的新闻��要，打破大数据推荐算法造成的信息茧房。

**三大核心能力：**
1. **对立视角** — 同一事件展示不同立场的报道（中西方媒体对比）
2. **盲区发现** — 主动推送用户平时不关注的领域和话题
3. **去噪精炼** — 过滤重复、低质、标题党内容

---

## 二、当前代码状态

### 已完成：后端（`backend/`）

```
backend/
├── app/
│   ├── main.py              ✅ FastAPI 入口（含 CORS、scheduler lifespan）
│   ├── config.py            ✅ Pydantic Settings（读取 .env）
│   ├── database.py          ✅ SQLAlchemy + get_db 依赖注入
│   ├── models/              ✅ 6张表：articles/topics/article_topics/digests/sources/pipeline_runs
│   ├── api/                 ✅ REST API：digest/topics/trigger/sources
│   ├── pipeline/
│   │   ├── state.py         ✅ PipelineState TypedDict
│   │   ├── graph.py         ✅ LangGraph 主图（5节点 + 数据持久化）
│   │   └── agents/          ✅ 5个Agent：collector/deduplicator/analyzer/aggregator/summarizer
│   └── scheduler.py         ✅ APScheduler 每晚20:00 定时触发
├── init_db.py               ✅ 建表 + 初始化5个新闻来源
├── .env.example             ✅ 配置模板
└── requirements.txt         ✅ 依赖列表
```

**测试状态：** `26 passed, 1 warning`（全部通过，warning 为预期行为）

### 待完成：前端（`frontend/`）

前端目录**尚未创建**，计划文档在 `docs/superpowers/plans/2026-03-25-frontend-startup.md`。

---

## 三、快速开始（新环境拉取后操作）

### 第一步：配置环境

```bash
# 1. 进入后端目录
cd backend

# 2. 创建 .env 文件（从模板复制）
cp .env.example .env

# 3. 编辑 .env，填入真实值
# 必填项：
#   MYSQL_URL=mysql+pymysql://root:你的密码@localhost:3306/akc_news
#   VOLC_API_KEY=你的火山引擎API Key
```

**`.env` 内容模板（填入真实值）：**
```
MYSQL_URL=mysql+pymysql://root:password@localhost:3306/akc_news
VOLC_API_KEY=你的火山引擎API Key
VOLC_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

MODEL_DOUBAO_LITE=ep-20250627102538-kbh7j
MODEL_DOUBAO_PRO=ep-20250627105312-62njr
MODEL_DEEPSEEK_R1=ep-20250627151708-wfrsp
MODEL_DEEPSEEK_V3=ep-20251222104545-wff8z
```

### 第二步：安装后端依赖

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

### 第三步：初始化数据库

```bash
# 先确保 MySQL 已启动，且 .env 中的 MYSQL_URL 正确
cd backend
python init_db.py
```

预期输出：
```
✓ 数据库表创建完成
✓ 初始化 5 个新闻来源
```

### 第四步：启动后端（验证）

```bash
cd backend
.venv\Scripts\uvicorn app.main:app --reload
```

访问 http://localhost:8000/health → 返回 `{"status": "ok"}`
访问 http://localhost:8000/docs → 查看所有 API

### 第五步：运行测试（可选验证）

```bash
cd backend
.venv\Scripts\pytest tests/ -v
```

预期：`26 passed, 1 warning`

---

## 四、下一步任务：实现前端

### 计划文档位置
```
docs/superpowers/plans/2026-03-25-frontend-startup.md
```

### 前端技术栈
- React 18 + TypeScript + Vite
- TailwindCSS + React Query (TanStack v5) + Axios
- react-markdown（渲染简报）
- react-router-dom（三页路由）

### 前端三个页面
1. **每日简报页（首页）** — 日期选择器 + Markdown 渲染 + 手动刷新按钮 + Pipeline 进度
2. **主题聚合页** — 事件包卡片列表（折叠/展开各方视角）+ 盲区筛选
3. **来源管理页** — 开关控制新闻来源启用/禁用

### 如何继续实现前端

打开 Claude Code，在 `d:/AKC/News` 目录下执行：

```
继续实现前端，计划文档在 docs/superpowers/plans/2026-03-25-frontend-startup.md，使用 subagent 驱动模式
```

Claude 会读取计划文档，派发子 Agent 逐步实现所有前端任务。

---

## 五、完整架构回顾

```
前端 (React)                           后端 (FastAPI :8000)
http://localhost:5173                  http://localhost:8000
────────────────                       ────────────────────
每日简报页    ──GET /api/digest──────→  digest.py
主题聚合页    ──GET /api/topics──────→  topics.py
             ──POST /api/trigger─────→  trigger.py（后台线程运行Pipeline）
来源管理页    ──GET/PUT /api/sources──→  sources.py

                                       LangGraph Pipeline
                                       ┌─────────────────────────────────┐
                                       │ 采集 → 去重 → 分析 → 聚合 → 总结 │
                                       └─────────────────────────────────┘
                                                     ↓
                                              MySQL 本地数据库
                                       articles / topics / digests / ...
```

### Agent 与模型对应关系
| Agent | 模型端点 | 职责 |
|-------|---------|------|
| 采集 | 无LLM | RSS/API拉取原始新闻 |
| 去重 | `ep-20250627102538-kbh7j`（Doubao-lite） | 语义去重 + 情感标注 |
| 分析 | `ep-20250627151708-wfrsp`（DeepSeek-R1） | 事件分组 + 盲区标记 |
| 聚合 | `ep-20251222104545-wff8z`（DeepSeek-V3.2） | 生成事件包 + 各方视角 |
| 总结 | `ep-20250627105312-62njr`（Doubao-pro） | 生成每日 Markdown 简报 |

---

## 六、重要文件位置

| 文件 | 说明 |
|------|------|
| `docs/superpowers/specs/2026-03-25-news-anti-bubble-design.md` | 完整设计规范文档 |
| `docs/superpowers/plans/2026-03-25-backend-pipeline.md` | 后端实施计划（已完成） |
| `docs/superpowers/plans/2026-03-25-frontend-startup.md` | 前端实施计划（待执行） |
| `backend/.env.example` | 环境变量模板 |
| `backend/init_db.py` | 数据库初始化脚本 |

---

## 七、Git 历史摘要

```
main 分支当前状态：
- 后端所有代码（42个文件，1153行新增）
- 26个测试全通过
- 待实现：frontend/ 目录
```

---

*本文档由 Claude Code 自动生成，用于跨设备开发交接。*
