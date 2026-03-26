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
