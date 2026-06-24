# Agent Meet 启动脚本
# 用法：.\start.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Agent Meet - AI 模拟面试系统启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 检查并启动 PostgreSQL + Redis
Write-Host "`n[1/4] 检查基础设施服务..." -ForegroundColor Yellow

$postgres = docker ps --filter "name=interview-postgres" --filter "status=running" --format "{{.Names}}" 2>$null
$redis = docker ps --filter "name=interview-redis" --filter "status=running" --format "{{.Names}}" 2>$null

if ($postgres -and $redis) {
    Write-Host "  PostgreSQL 和 Redis 已在运行" -ForegroundColor Green
} else {
    Write-Host "  正在启动 PostgreSQL 和 Redis..." -ForegroundColor Yellow
    Push-Location D:\vscode\project\interview-guide
    docker compose -f docker-compose.dev.yml up -d postgres redis
    Pop-Location
    Start-Sleep -Seconds 3
    Write-Host "  基础设施启动完成" -ForegroundColor Green
}

# 2. 检查 .env
Write-Host "`n[2/4] 检查环境配置..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "  .env 文件不存在，请先从 .env.example 复制并填入 API Key" -ForegroundColor Red
    Write-Host "  copy .env.example .env" -ForegroundColor DarkGray
    exit 1
} else {
    Write-Host "  .env 配置文件就绪" -ForegroundColor Green
}

# 3. 检查虚拟环境
Write-Host "`n[3/4] 检查 Python 环境..." -ForegroundColor Yellow

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "  虚拟环境不存在，正在创建..." -ForegroundColor Yellow
    python -m venv .venv
    .venv\Scripts\pip install -e ".[dev]" -q
    Write-Host "  虚拟环境创建完成" -ForegroundColor Green
} else {
    Write-Host "  虚拟环境就绪" -ForegroundColor Green
}

# 4. 启动应用
Write-Host "`n[4/4] 启动 Agent Meet 应用..." -ForegroundColor Yellow
Write-Host "  访问地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  按 Ctrl+C 停止`n" -ForegroundColor DarkGray

.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
#uvicorn app.main:app
