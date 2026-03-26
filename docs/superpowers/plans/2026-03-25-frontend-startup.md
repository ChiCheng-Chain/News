# 打破信息茧房 · 前端 + 启动脚本实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 React Web 前端，包含每日简报页（含历史日期选择）、主题聚合卡片页、来源管理页，以及一键启动全栈的 `start.bat` 脚本。

**Architecture:** React + Vite SPA，用 React Query 管理服务端状态和缓存，Axios 封装 API 调用，TailwindCSS 负责样式。前端通过 `?date=YYYY-MM-DD` 参数支持历史回溯查询。

**Tech Stack:** React 18, TypeScript, Vite, TailwindCSS, React Query (TanStack Query v5), Axios, react-markdown

**依赖：** 本计划依赖 Plan 1（后端）完成并可运行：`http://localhost:8000`

**Spec:** `docs/superpowers/specs/2026-03-25-news-anti-bubble-design.md`

---

## 文件结构

```
frontend/
├── src/
│   ├── main.tsx                    # React 入口
│   ├── App.tsx                     # 路由配置
│   ├── api/
│   │   └── client.ts               # Axios 实例 + 所有API函数
│   ├── pages/
│   │   ├── DigestPage.tsx          # 每日简报页（首页）
│   │   ├── TopicsPage.tsx          # 主题聚合页
│   │   └── SourcesPage.tsx         # 来源管理页
│   └── components/
│       ├── DatePicker.tsx          # 日期选择器（今天/历史切换）
│       ├── TopicCard.tsx           # 事件包卡片（折叠/展开）
│       ├── PipelineStatus.tsx      # Pipeline运行进度条
│       └── NavBar.tsx              # 顶部导航
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts

start.bat                           # 根目录，一键启动脚本
```

---

## Task 1: 前端项目初始化

**Files:**
- Create: `frontend/` 目录及配置文件

- [ ] **Step 1: 用 Vite 创建 React + TypeScript 项目**

```bash
cd d:/AKC/News
npm create vite@latest frontend -- --template react-ts
cd frontend
```

- [ ] **Step 2: 安装依赖**

```bash
npm install
npm install @tanstack/react-query axios react-markdown react-router-dom
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 3: 配置 TailwindCSS**

编辑 `frontend/tailwind.config.js`：

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

编辑 `frontend/src/index.css`，替换全部内容：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 4: 配置 Vite 代理（开发时转发API请求到后端）**

编辑 `frontend/vite.config.ts`：

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 5: 验证项目启动**

```bash
npm run dev
```

Expected: 浏览器访问 http://localhost:5173 显示 Vite 默认页面

- [ ] **Step 6: Commit**

```bash
cd d:/AKC/News
git add frontend/
git commit -m "chore: 初始化前端项目（React + Vite + TailwindCSS）"
```

---

## Task 2: API 客户端层

**Files:**
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: 编写 client.ts**

```ts
// frontend/src/api/client.ts
import axios from 'axios'

const http = axios.create({ baseURL: '/' })

export interface Digest {
  id: number
  date: string
  content: string
  triggered_by: string
  created_at: string
}

export interface Perspective {
  source: string
  stance: string
  summary: string
}

export interface Topic {
  id: number
  title: string
  summary: string
  perspectives: Perspective[]
  is_blind_spot: boolean
  date: string
}

export interface Source {
  id: number
  name: string
  type: string
  url: string
  language: string
  enabled: boolean
}

export interface PipelineStatus {
  status: 'idle' | 'running' | 'done' | 'failed'
  current_step: string | null
  started_at: string | null
  finished_at: string | null
  error_msg: string | null
}

export const api = {
  getDigest: (date?: string) =>
    http.get<Digest>('/api/digest', { params: date ? { date } : {} }).then(r => r.data),

  getTopics: (date?: string) =>
    http.get<Topic[]>('/api/topics', { params: date ? { date } : {} }).then(r => r.data),

  getTopic: (id: number) =>
    http.get<Topic>(`/api/topics/${id}`).then(r => r.data),

  triggerPipeline: () =>
    http.post('/api/trigger').then(r => r.data),

  getPipelineStatus: () =>
    http.get<PipelineStatus>('/api/pipeline/status').then(r => r.data),

  getSources: () =>
    http.get<Source[]>('/api/sources').then(r => r.data),

  updateSource: (id: number, enabled: boolean) =>
    http.put<Source>(`/api/sources/${id}`, { enabled }).then(r => r.data),
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/
git commit -m "feat: 添加前端API客户端层"
```

---

## Task 3: 基础组件

**Files:**
- Create: `frontend/src/components/NavBar.tsx`
- Create: `frontend/src/components/DatePicker.tsx`
- Create: `frontend/src/components/PipelineStatus.tsx`
- Create: `frontend/src/components/TopicCard.tsx`

- [ ] **Step 1: 编写 NavBar.tsx**

```tsx
// frontend/src/components/NavBar.tsx
import { Link, useLocation } from 'react-router-dom'

export function NavBar() {
  const { pathname } = useLocation()
  const links = [
    { to: '/', label: '每日简报' },
    { to: '/topics', label: '主题聚合' },
    { to: '/sources', label: '来源管理' },
  ]
  return (
    <nav className="bg-gray-900 text-white px-6 py-3 flex items-center gap-8">
      <span className="font-bold text-lg">🌐 打破信息茧房</span>
      <div className="flex gap-6">
        {links.map(l => (
          <Link
            key={l.to}
            to={l.to}
            className={`text-sm hover:text-blue-300 transition-colors ${
              pathname === l.to ? 'text-blue-400 font-medium' : 'text-gray-300'
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
```

- [ ] **Step 2: 编写 DatePicker.tsx**

```tsx
// frontend/src/components/DatePicker.tsx
interface DatePickerProps {
  value: string   // YYYY-MM-DD
  onChange: (date: string) => void
}

export function DatePicker({ value, onChange }: DatePickerProps) {
  const today = new Date().toISOString().split('T')[0]
  return (
    <div className="flex items-center gap-3">
      <input
        type="date"
        value={value}
        max={today}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      {value !== today && (
        <button
          onClick={() => onChange(today)}
          className="text-xs text-blue-500 hover:underline"
        >
          回到今天
        </button>
      )}
    </div>
  )
}
```

- [ ] **Step 3: 编写 PipelineStatus.tsx**

```tsx
// frontend/src/components/PipelineStatus.tsx
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const STEP_LABELS: Record<string, string> = {
  collect: '采集新闻',
  deduplicate: '去重过滤',
  analyze: '分析视角',
  aggregate: '聚合事件',
  summarize: '生成简报',
  done: '完成',
}

export function PipelineStatus() {
  const { data } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: api.getPipelineStatus,
    refetchInterval: (data) =>
      data?.state?.data?.status === 'running' ? 3000 : false,
  })

  if (!data || data.status === 'idle' || data.status === 'done') return null

  if (data.status === 'failed') {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
        Pipeline 运行失败：{data.error_msg}
      </div>
    )
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-700 flex items-center gap-2">
      <span className="animate-spin">⏳</span>
      正在运行：{STEP_LABELS[data.current_step ?? ''] ?? data.current_step}
    </div>
  )
}
```

- [ ] **Step 4: 编写 TopicCard.tsx**

```tsx
// frontend/src/components/TopicCard.tsx
import { useState } from 'react'
import type { Topic } from '../api/client'

interface TopicCardProps {
  topic: Topic
}

export function TopicCard({ topic }: TopicCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {topic.is_blind_spot && (
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">盲区</span>
            )}
            <h3 className="font-medium text-gray-900">{topic.title}</h3>
          </div>
          <p className="text-sm text-gray-600">{topic.summary}</p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-500 hover:underline whitespace-nowrap"
        >
          {expanded ? '收起' : `查看 ${topic.perspectives?.length ?? 0} 个视角`}
        </button>
      </div>

      {expanded && topic.perspectives?.length > 0 && (
        <div className="mt-3 space-y-2 border-t pt-3">
          {topic.perspectives.map((p, i) => (
            <div key={i} className="bg-gray-50 rounded p-3">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-gray-500">{p.source}</span>
                <span className="text-xs text-gray-400">·</span>
                <span className="text-xs text-gray-500">{p.stance}</span>
              </div>
              <p className="text-sm text-gray-700">{p.summary}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: 添加NavBar、DatePicker、PipelineStatus、TopicCard组件"
```

---

## Task 4: 每日简报页（首页）

**Files:**
- Create: `frontend/src/pages/DigestPage.tsx`

- [ ] **Step 1: 编写 DigestPage.tsx**

```tsx
// frontend/src/pages/DigestPage.tsx
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import { api } from '../api/client'
import { DatePicker } from '../components/DatePicker'
import { PipelineStatus } from '../components/PipelineStatus'

export function DigestPage() {
  const today = new Date().toISOString().split('T')[0]
  const [selectedDate, setSelectedDate] = useState(today)
  const queryClient = useQueryClient()

  const { data: digest, isLoading, isError } = useQuery({
    queryKey: ['digest', selectedDate],
    queryFn: () => api.getDigest(selectedDate),
    retry: false,
  })

  const triggerMutation = useMutation({
    mutationFn: api.triggerPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-status'] })
    },
  })

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <DatePicker value={selectedDate} onChange={setSelectedDate} />
        {selectedDate === today && (
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={triggerMutation.isPending}
            className="text-sm bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {triggerMutation.isPending ? '启动中...' : '立即刷新'}
          </button>
        )}
      </div>

      <PipelineStatus />

      {triggerMutation.isError && (
        <div className="my-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
          {(triggerMutation.error as any)?.response?.data?.detail ?? '触发失败，请稍后重试'}
        </div>
      )}

      <div className="mt-4">
        {isLoading && <p className="text-gray-500 text-sm">加载中...</p>}
        {isError && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-3">📭</p>
            <p>{selectedDate} 暂无简报</p>
            {selectedDate === today && (
              <p className="text-sm mt-1">点击右上角「立即刷新」生成今日简报</p>
            )}
          </div>
        )}
        {digest && (
          <article className="prose prose-gray max-w-none">
            <ReactMarkdown>{digest.content}</ReactMarkdown>
          </article>
        )}
      </div>
    </div>
  )
}
```

> 注意：`prose` 样式需要安装 `@tailwindcss/typography`：
> ```bash
> npm install -D @tailwindcss/typography
> ```
> 并在 `tailwind.config.js` 的 plugins 中加入：`require('@tailwindcss/typography')`

- [ ] **Step 2: 安装 typography 插件**

```bash
cd frontend
npm install -D @tailwindcss/typography
```

编辑 `frontend/tailwind.config.js`，plugins 改为：
```js
plugins: [require('@tailwindcss/typography')],
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DigestPage.tsx frontend/tailwind.config.js
git commit -m "feat: 实现每日简报页（含日期选择器和手动触发）"
```

---

## Task 5: 主题聚合页

**Files:**
- Create: `frontend/src/pages/TopicsPage.tsx`

- [ ] **Step 1: 编写 TopicsPage.tsx**

```tsx
// frontend/src/pages/TopicsPage.tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { DatePicker } from '../components/DatePicker'
import { TopicCard } from '../components/TopicCard'

export function TopicsPage() {
  const today = new Date().toISOString().split('T')[0]
  const [selectedDate, setSelectedDate] = useState(today)
  const [showBlindSpotOnly, setShowBlindSpotOnly] = useState(false)

  const { data: topics = [], isLoading } = useQuery({
    queryKey: ['topics', selectedDate],
    queryFn: () => api.getTopics(selectedDate),
  })

  const filtered = showBlindSpotOnly ? topics.filter(t => t.is_blind_spot) : topics

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <DatePicker value={selectedDate} onChange={setSelectedDate} />
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={showBlindSpotOnly}
            onChange={e => setShowBlindSpotOnly(e.target.checked)}
            className="rounded"
          />
          只看盲区话题
        </label>
      </div>

      {isLoading && <p className="text-gray-500 text-sm">加载中...</p>}

      {!isLoading && filtered.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🗂️</p>
          <p>{selectedDate} 暂无主题数据</p>
        </div>
      )}

      <div className="space-y-3">
        {filtered.map(topic => (
          <TopicCard key={topic.id} topic={topic} />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/TopicsPage.tsx
git commit -m "feat: 实现主题聚合页（含盲区筛选）"
```

---

## Task 6: 来源管理页

**Files:**
- Create: `frontend/src/pages/SourcesPage.tsx`

- [ ] **Step 1: 编写 SourcesPage.tsx**

```tsx
// frontend/src/pages/SourcesPage.tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export function SourcesPage() {
  const queryClient = useQueryClient()

  const { data: sources = [], isLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: api.getSources,
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      api.updateSource(id, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-lg font-semibold text-gray-900 mb-4">新闻来源管理</h1>

      {isLoading && <p className="text-gray-500 text-sm">加载中...</p>}

      <div className="space-y-2">
        {sources.map(source => (
          <div
            key={source.id}
            className="flex items-center justify-between border border-gray-200 rounded-lg px-4 py-3"
          >
            <div>
              <p className="font-medium text-sm text-gray-900">{source.name}</p>
              <p className="text-xs text-gray-400">
                {source.type.toUpperCase()} · {source.language}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={source.enabled}
                onChange={e =>
                  toggleMutation.mutate({ id: source.id, enabled: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-10 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:bg-blue-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-4" />
            </label>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/SourcesPage.tsx
git commit -m "feat: 实现来源管理页（开关启用/禁用）"
```

---

## Task 7: 路由 & 入口

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: 编写 App.tsx**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NavBar } from './components/NavBar'
import { DigestPage } from './pages/DigestPage'
import { TopicsPage } from './pages/TopicsPage'
import { SourcesPage } from './pages/SourcesPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <NavBar />
          <main>
            <Routes>
              <Route path="/" element={<DigestPage />} />
              <Route path="/topics" element={<TopicsPage />} />
              <Route path="/sources" element={<SourcesPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

- [ ] **Step 2: 编写 main.tsx**

```tsx
// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 3: 删除 Vite 默认文件**

```bash
rm frontend/src/App.css
rm frontend/src/assets/react.svg
```

- [ ] **Step 4: 验证前端完整运行**

```bash
cd frontend
npm run dev
```

访问 http://localhost:5173，验证：
- 三个页面可以导航
- 每日简报页显示"暂无简报"（后端未运行时）
- 日期选择器可以切换日期
- 来源管理页显示来源列表（需后端运行）

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat: 完成前端路由配置和入口，前端应用可完整运行"
```

---

## Task 8: 一键启动脚本

**Files:**
- Create: `start.bat`（根目录）

- [ ] **Step 1: 编写 start.bat**

```bat
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo    打破信息茧房 - 一键启动脚本
echo ============================================
echo.

:: ---- 检查 Python 3.12 ----
set PYTHON_CMD=
for %%p in (python3.12 python3 python) do (
    if "!PYTHON_CMD!"=="" (
        %%p --version 2>nul | findstr /r "3\.12" >nul 2>&1
        if !errorlevel! == 0 set PYTHON_CMD=%%p
    )
)
if "!PYTHON_CMD!"=="" (
    echo [错误] 未找到 Python 3.12，请先安装：https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 3.12 已就绪（命令：!PYTHON_CMD!）

:: ---- 检查 Node.js ----
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装：https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js 已就绪

:: ---- 检查后端 .env ----
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo.
        echo [提示] 已创建 backend\.env，请编辑该文件填入：
        echo        - MYSQL_URL（本地MySQL连接串）
        echo        - VOLC_API_KEY（火山引擎API Key）
        echo.
        echo 填写完成后重新运行此脚本。
        notepad "backend\.env"
        pause
        exit /b 0
    ) else (
        echo [错误] 未找到 backend\.env 和 backend\.env.example
        pause
        exit /b 1
    )
)
echo [OK] backend\.env 已就绪

:: ---- 创建/激活后端虚拟环境 ----
if not exist "backend\.venv\Scripts\activate.bat" (
    echo [安装] 创建 Python 虚拟环境...
    cd backend
    !PYTHON_CMD! -m venv .venv
    cd ..
)
echo [OK] 虚拟环境已就绪

:: ---- 安装/更新后端依赖 ----
echo [检查] 后端依赖...
backend\.venv\Scripts\pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [安装] 安装后端依赖（首次可能需要几分钟）...
    backend\.venv\Scripts\pip install -r backend\requirements.txt -q
    if errorlevel 1 (
        echo [错误] 后端依赖安装失败
        pause
        exit /b 1
    )
)
echo [OK] 后端依赖已就绪

:: ---- 初始化数据库（仅首次）----
echo [检查] 数据库初始化...
cd backend
.venv\Scripts\python init_db.py
if errorlevel 1 (
    echo [错误] 数据库初始化失败，请检查 MYSQL_URL 是否正确
    cd ..
    pause
    exit /b 1
)
cd ..

:: ---- 安装前端依赖 ----
if not exist "frontend\node_modules" (
    echo [安装] 安装前端依赖（首次可能需要几分钟）...
    cd frontend
    npm install --silent
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        cd ..
        pause
        exit /b 1
    )
    cd ..
)
echo [OK] 前端依赖已就绪

:: ---- 启动后端（新窗口）----
echo.
echo [启动] 后端服务（http://localhost:8000）...
start "后端服务" cmd /k "cd /d %~dp0backend && .venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: ---- 启动前端（新窗口）----
echo [启动] 前端服务（http://localhost:5173）...
start "前端服务" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo   启动完成！
echo   前端：http://localhost:5173
echo   后端API文档：http://localhost:8000/docs
echo ============================================
echo.
echo 关闭此窗口不会停止服务，请在对应窗口按 Ctrl+C 停止。
pause
```

- [ ] **Step 2: 验证脚本（在项目根目录）**

```bash
# 先在 WSL/PowerShell 中检查格式，确保Windows换行符
# 直接在 Windows 上双击 start.bat 验证
```

在 Windows 文件管理器中双击 `start.bat`，预期流程：
1. 检测 Python 3.12 → 显示 `[OK]`
2. 检测 Node.js → 显示 `[OK]`
3. 检测 `.env` → 已存在则 `[OK]`
4. 创建/检测虚拟环境 → `[OK]`
5. 安装依赖 → `[OK]`
6. 初始化数据库 → `✓ 数据库表创建完成`
7. 打开两个新 CMD 窗口分别运行后端和前端
8. 显示访问地址

- [ ] **Step 3: Commit**

```bash
git add start.bat
git commit -m "feat: 添加一键启动脚本（环境检查+自动安装+双窗口启动）"
```

---

## 验收标准

前端 + 启动脚本完成后，应满足：

1. 双击 `start.bat` 无报错，自动打开前后端两个服务窗口
2. 首次运行自动安装依赖并初始化数据库
3. `.env` 不存在时自动弹出编辑提示，再次运行正常启动
4. 访问 http://localhost:5173 显示完整的三页面导航
5. 每日简报页：日期选择器可切换历史日期，3.8日的数据和今天的数据均可查询
6. 主题聚合页：卡片展开显示各方视角，"只看盲区"筛选有效
7. 来源管理页：开关可以成功启用/禁用来源
8. 手动触发按钮在后端运行时显示进度状态

---

**整体项目完成！**

后续可考虑扩展（Phase 2）：
- 用户行为记录 → 真正的"盲区发现"个性化
- 微信公众号 RSS 代理配置
- NewsAPI / GDELT API 类型来源接入
