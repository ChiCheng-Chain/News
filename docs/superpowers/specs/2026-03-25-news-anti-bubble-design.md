# 打破信息茧房 · 新闻聚合系统设计文档

**日期：** 2026-03-25
**状态：** 已确认
**技术栈：** Python 3.12 + FastAPI + LangGraph + React + MySQL

---

## 一、项目目标

构建一个前后端系统，通过多 Agent 协同，每天为用户生成精炼、多元视角的新闻摘要，主动打破大数据推荐算法造成的信息茧房。

**三大核心能力：**
1. **对立视角**——同一事件展示不同立场的报道（如中西方媒体对同一事件的不同叙述）
2. **盲区发现**——主动推送用户平时不关注的领域和话题
3. **去噪精炼**——过滤重复、低质、标题党内容，只留真正有价值的新闻

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────┐
│                    前端 (React)                      │
│   每日简报页 | 主题聚合卡片 | 来源管理页             │
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────┐
│                 后端 (FastAPI)                       │
│   /api/digest  /api/topics  /api/trigger  /api/sources │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              LangGraph Pipeline                      │
│                                                      │
│  [采集Agent] → [去重Agent] → [分析Agent]             │
│                                   ↓                 │
│                       [聚合Agent] → [总结Agent]      │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  MySQL（本地）                        │
│  articles | topics | article_topics | digests        │
│  sources | pipeline_runs                             │
└─────────────────────────────────────────────────────┘
```

---

## 三、LangGraph Pipeline · Agent 职责

| Agent | 模型 | 职责 |
|-------|------|------|
| **采集Agent** | 无需LLM | RSS/API拉取原始新闻，支持：NewsAPI、GDELT、BBC/Reuters RSS、微信公众号RSS代理 |
| **去重/过滤Agent** | `Doubao-lite-128k`（ep-20250627102538-kbh7j） | 语义去重、过滤标题党/低质量内容、提取关键元数据 |
| **分析Agent** | `DeepSeek-R1`（ep-20250627151708-wfrsp） | ① 识别同一事件的不同立场报道 ② 标记盲区话题 ③ 情感倾向分析 |
| **聚合Agent** | `DeepSeek-V3.2`（ep-20251222104545-wff8z） | 将同一事件的多方报道聚合为"事件包" |
| **总结Agent** | `Doubao-pro-128k`（ep-20250627105312-62njr） | 生成每日简报：结构化文章，含重大事件、对立视角、盲区推送 |

**模型分工逻辑：**
- R1：最需要推理的分析节点（质量优先）
- Doubao-lite：高频简单过滤（速度和成本优先）
- Doubao-pro：最终输出（质量优先）
- DeepSeek-V3.2：结构化聚合（平衡质量与成本）

**备用模型：**
- DeepSeek-V3.1（ep-20250901170033-qhvdd）：可在V3.2不可用时替换

---

## 四、数据模型（MySQL）

```sql
-- 原始文章
CREATE TABLE articles (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  source VARCHAR(100),
  title VARCHAR(500),
  content LONGTEXT,
  url VARCHAR(1000),
  published_at DATETIME,
  language VARCHAR(10),
  sentiment ENUM('positive', 'negative', 'neutral'),
  is_duplicate BOOLEAN DEFAULT FALSE,
  date DATE,
  created_at DATETIME DEFAULT NOW()
);

-- 主题事件包
CREATE TABLE topics (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(500),
  summary TEXT,
  perspectives JSON,       -- [{"source":"BBC","stance":"西方视角","summary":"..."}]
  is_blind_spot BOOLEAN DEFAULT FALSE,
  date DATE,
  created_at DATETIME DEFAULT NOW()
);

-- 文章与主题关联
CREATE TABLE article_topics (
  article_id BIGINT,
  topic_id BIGINT,
  viewpoint_label VARCHAR(100)
);

-- 每日简报
CREATE TABLE digests (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  date DATE UNIQUE,
  content LONGTEXT,
  topic_ids JSON,
  triggered_by ENUM('scheduled', 'manual'),
  created_at DATETIME DEFAULT NOW()
);

-- 新闻来源
CREATE TABLE sources (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100),
  type ENUM('rss', 'api'),
  url VARCHAR(500),
  language VARCHAR(10),
  enabled BOOLEAN DEFAULT TRUE
);

-- Pipeline运行记录
CREATE TABLE pipeline_runs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  date DATE,
  status ENUM('running', 'done', 'failed'),
  current_step VARCHAR(50),
  started_at DATETIME,
  finished_at DATETIME,
  error_msg TEXT
);
```

---

## 五、REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/digest?date=YYYY-MM-DD` | 获取指定日期简报（默认今天） |
| GET | `/api/topics?date=YYYY-MM-DD` | 获取指定日期事件包列表 |
| GET | `/api/topics/{id}` | 获取单个事件包详情 |
| POST | `/api/trigger` | 手动触发Pipeline（同天已运行返回409） |
| GET | `/api/pipeline/status` | 查询当前Pipeline运行状态 |
| GET | `/api/sources` | 获取来源列表 |
| PUT | `/api/sources/{id}` | 启用/禁用来源 |

---

## 六、调度机制

- **定时任务**：APScheduler 内嵌于 FastAPI，每晚 20:00 自动触发（cron: `0 20 * * *`）
- **手动触发**：`POST /api/trigger`，调用同一 Pipeline 函数
- **防重复**：同天已有 `running` 状态时返回 409
- **进度追踪**：Pipeline 每步更新 `pipeline_runs.current_step`，前端轮询展示进度

---

## 七、前端页面

### 每日简报页（首页）
- 顶部日期选择器，默认今天，可切换历史日期
- Markdown 渲染简报内容
- "立即刷新"按钮（仅当天有效）
- 显示触发方式 + 运行时间戳
- Pipeline 运行中显示步骤进度

### 主题聚合页
- 顶部日期选择器
- 事件包卡片列表：主标题 + 各方视角摘要 + 来源标签
- 筛选：按日期、按是否盲区话题
- 点击卡片展开详情，显示完整各方报道对比

### 来源管理页
- 来源列表，开关控制启用/禁用

**技术选型：** React + Vite + TailwindCSS + React Query + Axios

---

## 八、项目结构

```
News/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── pipeline/
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   └── agents/
│   │   │       ├── collector.py
│   │   │       ├── deduplicator.py
│   │   │       ├── analyzer.py
│   │   │       ├── aggregator.py
│   │   │       └── summarizer.py
│   │   ├── models/
│   │   ├── scheduler.py
│   │   └── config.py
│   ├── .env
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── DigestPage.tsx
│   │   │   ├── TopicsPage.tsx
│   │   │   └── SourcesPage.tsx
│   │   ├── components/
│   │   └── api/
│   ├── package.json
│   └── vite.config.ts
├── start.bat
└── README.md
```

---

## 九、一键启动脚本（start.bat）

**执行逻辑：**
1. 检查 Python 3.12 是否存在
2. 检查 `backend/.venv` → 不存在则创建虚拟环境
3. 检查依赖 → 对比 requirements.txt，缺失则安装
4. 检查 `backend/.env` → 不存在则从 `.env.example` 复制并提示填写后退出
5. 检查 Node.js 是否存在
6. 检查 `frontend/node_modules` → 不存在则 `npm install`
7. 双窗口分别启动后端（uvicorn）和前端（vite）
8. 打印访问地址：`http://localhost:5173`

**`.env.example`：**
```
MYSQL_URL=mysql+pymysql://root:password@localhost:3306/akc_news
VOLC_API_KEY=你的豆包API Key
VOLC_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

---

## 十、新闻来源（初始配置）

| 来源 | 类型 | 语言 |
|------|------|------|
| NewsAPI | API | 中/英 |
| GDELT | API | 多语言 |
| BBC News RSS | RSS | 英文 |
| Reuters RSS | RSS | 英文 |
| 微信公众号RSS代理 | RSS | 中文 |
