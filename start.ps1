# Agent Meet startup script
# Usage: .\start.ps1

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Agent Meet - AI Interview System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Check Docker
Write-Host ""
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow

$dockerRunning = $false
try {
    docker info 2>&1 | Out-Null
    $dockerRunning = $true
} catch {
    $dockerRunning = $false
}

if (-not $dockerRunning) {
    Write-Host "  Docker not running, starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "  Waiting for Docker (max 60s)..." -ForegroundColor Yellow
    $timeout = 60
    while ($timeout -gt 0) {
        Start-Sleep -Seconds 2
        $timeout -= 2
        $check = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerRunning = $true
            break
        }
    }
}

if ($dockerRunning) {
    Write-Host "  Docker is ready" -ForegroundColor Green
} else {
    Write-Host "  Docker startup timeout" -ForegroundColor Red
    exit 1
}

# 2. Start PostgreSQL + Redis
Write-Host ""
Write-Host "[2/4] Starting PostgreSQL and Redis..." -ForegroundColor Yellow

$postgres = (docker ps --filter "name=agent-meet-postgres" --filter "status=running" --format "{{.Names}}" 2>&1) | Out-String
$redis = (docker ps --filter "name=agent-meet-redis" --filter "status=running" --format "{{.Names}}" 2>&1) | Out-String

if ($postgres -and $redis) {
    Write-Host "  PostgreSQL and Redis already running" -ForegroundColor Green
} else {
    docker compose -f docker-compose.dev.yml up -d
    Write-Host "  Waiting for services..." -ForegroundColor Yellow

    # Wait for PostgreSQL
    for ($i = 0; $i -lt 30; $i++) {
        $result = docker exec agent-meet-postgres pg_isready -U postgres 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  PostgreSQL is ready" -ForegroundColor Green
            break
        }
        Start-Sleep -Seconds 1
    }

    # Wait for Redis
    for ($i = 0; $i -lt 15; $i++) {
        $result = docker exec agent-meet-redis redis-cli ping 2>&1
        if ($result -match "PONG") {
            Write-Host "  Redis is ready" -ForegroundColor Green
            break
        }
        Start-Sleep -Seconds 1
    }
}

# 3. Check .env
Write-Host ""
Write-Host "[3/4] Checking .env config..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "  .env file not found, copy from .env.example first" -ForegroundColor Red
    Write-Host "  copy .env.example .env" -ForegroundColor DarkGray
    exit 1
} else {
    Write-Host "  .env is ready" -ForegroundColor Green
}

# 4. Start app
Write-Host ""
Write-Host "[4/4] Starting Agent Meet..." -ForegroundColor Yellow
Write-Host "  URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host ""

uvicorn app.main:app --reload --reload-exclude ".venv"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# .\start.ps1
