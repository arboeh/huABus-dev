# run_local.ps1 - Local development runner (PowerShell)

param(
    [switch]$Test,
    [switch]$Coverage,
    [switch]$Shell
)

# ===== GET SCRIPT AND ROOT DIRECTORY =====
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir  # Ein Level höher (Root)

# ===== CHECK VIRTUAL ENVIRONMENT =====
uv sync --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  uv sync failed - retrying..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    uv sync --quiet
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ uv sync failed!" -ForegroundColor Red
    exit 1
}

# ===== TEST MODE =====
if ($Test -or $Shell) {
    Write-Host "🧪 Running tests..." -ForegroundColor Yellow

    # uv sync vor Tests (reproduzierbar)
    uv sync --all-extras
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Dependency sync failed!" -ForegroundColor Red
        exit 1
    }

    # Wechsel ins Root-Verzeichnis für pytest
    Push-Location $rootDir

    if ($Shell) {
        # ===== BATS TESTS =====

        $batsDir = Join-Path $rootDir ".tools\bats-core"
        $batsBin = Join-Path $batsDir "bin\bats"

        # Install bats-core locally if missing
        if (!(Test-Path $batsBin)) {
            Write-Host "📦 Installing bats-core locally..." -ForegroundColor Yellow

            if (!(Test-Path $batsDir)) {
                git clone https://github.com/bats-core/bats-core.git $batsDir
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "❌ Failed to clone bats-core!" -ForegroundColor Red
                    exit 1
                }
            }

            # Fix CRLF → LF (Windows git issue)
            Write-Host "🔧 Fixing line endings..." -ForegroundColor Yellow

            Get-ChildItem $batsDir -Recurse -File | ForEach-Object {
                (Get-Content $_.FullName -Raw) -replace "`r`n","`n" | Set-Content $_.FullName -NoNewline
            }
        }

        # Ensure bash exists
        if (!(Get-Command bash -ErrorAction SilentlyContinue)) {
            Write-Host "❌ bash not found. Install Git for Windows." -ForegroundColor Red
            exit 1
        }

        Write-Host "🐚 Running BATS tests..." -ForegroundColor Cyan

        $batsExe = (Get-Command bash.exe).Source
        & $batsExe "$batsBin" tests/test_run.bats

        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ BATS tests failed!" -ForegroundColor Red
            exit $LASTEXITCODE
        }

        Write-Host "✅ BATS tests passed!" -ForegroundColor Green
    }
    elseif ($Coverage) {
        uv run pytest -v --cov=huawei_solar_modbus_mqtt/bridge --cov-report=html
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ All tests passed!" -ForegroundColor Green
            Write-Host "📊 Opening coverage report..." -ForegroundColor Cyan
            Start-Process htmlcov/index.html
        }
        else {
            Write-Host "❌ Tests failed!" -ForegroundColor Red
        }
    }
    else {
        uv run pytest tests -v
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ All tests passed!" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Tests failed!" -ForegroundColor Red
        }
    }

    Pop-Location
    exit $LASTEXITCODE
}


# ===== NORMAL MODE =====
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🚀 huABus - Local Development" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan

# Load .env (besseres Parsing)
$envPath = Join-Path $rootDir ".env"
if (Test-Path $envPath) {
    Write-Host "📄 Loading .env" -ForegroundColor Blue
    Get-Content $envPath | ForEach-Object {
        $line = $_.Trim()
        # Skip comments and empty lines
        if ($line -and !$line.StartsWith('#')) {
            if ($line -match '^([^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                Set-Item -Path "env:$key" -Value $value
                Write-Host "  $key = $value" -ForegroundColor DarkGray
            }
        }
    }
}
else {
    Write-Host "❌ No .env file in root directory!" -ForegroundColor Red
    Write-Host "   Expected: $envPath" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ">> System Info:" -ForegroundColor Blue

# Python version
$pythonVersion = python --version 2>&1 | Select-String -Pattern "Python (\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
Write-Host "   - Python: $pythonVersion" -ForegroundColor White

# Get version from version.py
try {
    $versionPath = Join-Path $rootDir "huawei_solar_modbus_mqtt\bridge\version.py"
    if (Test-Path $versionPath) {
        $versionContent = Get-Content $versionPath | Select-String 'version\s*=\s*"([^"]+)"'
        if ($versionContent) {
            $appVersion = $versionContent.Matches.Groups[1].Value
        }
        else {
            $appVersion = "dev"
        }
    }
    else {
        $appVersion = "dev"
        Write-Host "   [DEBUG] version.py not found at: $versionPath" -ForegroundColor DarkYellow
    }
}
catch {
    $appVersion = "dev"
    Write-Host "   [DEBUG] Error reading version.py: $_" -ForegroundColor Red
}

Write-Host "   - App-Version: $appVersion" -ForegroundColor Cyan

# Register count
try {
    # Wechsel ins Addon-Verzeichnis für den Import
    Push-Location (Join-Path $rootDir "huawei_solar_modbus_mqtt")
    $registerCount = python -c "from bridge.config.registers import ESSENTIAL_REGISTERS; print(len(ESSENTIAL_REGISTERS))" 2>$null
    Pop-Location

    if ($registerCount -and $registerCount -match '^\d+$') {
        Write-Host "   - Registers: $registerCount essential" -ForegroundColor White
    }
    else {
        Write-Host "   - Registers: unknown" -ForegroundColor DarkGray
    }
}
catch {
    Pop-Location  # Sicherstellen, dass wir zurückwechseln
    Write-Host "   - Registers: unknown" -ForegroundColor DarkGray
}

# Package versions
try {
    $huaweiVersion = pip show huawei-solar 2>$null | Select-String "^Version:" | ForEach-Object { $_.ToString().Split(":")[1].Trim() }
    if (!$huaweiVersion) { $huaweiVersion = "unknown" }
}
catch { $huaweiVersion = "unknown" }

try {
    $pymodbusVersion = pip show pymodbus 2>$null | Select-String "^Version:" | ForEach-Object { $_.ToString().Split(":")[1].Trim() }
    if (!$pymodbusVersion) { $pymodbusVersion = "unknown" }
}
catch { $pymodbusVersion = "unknown" }

try {
    $pahoVersion = pip show paho-mqtt 2>$null | Select-String "^Version:" | ForEach-Object { $_.ToString().Split(":")[1].Trim() }
    if (!$pahoVersion) { $pahoVersion = "unknown" }
}
catch { $pahoVersion = "unknown" }

Write-Host "   - huawei-solar: $huaweiVersion" -ForegroundColor White
Write-Host "   - pymodbus: $pymodbusVersion" -ForegroundColor White
Write-Host "   - paho-mqtt: $pahoVersion" -ForegroundColor White

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ">> Configuration:" -ForegroundColor Blue
Write-Host "   🔌 Inverter: $env:HUAWEI_MODBUS_HOST`:$env:HUAWEI_MODBUS_PORT (Slave ID: $env:HUAWEI_SLAVE_ID)" -ForegroundColor White
Write-Host "   📡 MQTT    : $env:HUAWEI_MQTT_HOST`:$env:HUAWEI_MQTT_PORT" -ForegroundColor White
Write-Host "   📍 Topic   : $env:HUAWEI_MQTT_TOPIC" -ForegroundColor White
Write-Host "   ⏱️  Poll    : $env:HUAWEI_POLL_INTERVAL`s | Timeout: $env:HUAWEI_STATUS_TIMEOUT`s" -ForegroundColor White
if ($env:HUAWEI_ENABLE_CACHING -eq "True" -or $env:HUAWEI_ENABLE_CACHING -eq "true") {
    Write-Host "   💾 Cache   : enabled | max_age=$env:HUAWEI_CACHE_MAX_AGE`s (MQTT heartbeat every second)" -ForegroundColor White
}
else {
    Write-Host "   💾 Cache   : disabled" -ForegroundColor White
}
Write-Host "   📍 Log     : $env:HUAWEI_LOG_LEVEL" -ForegroundColor White
Write-Host "========================================================================" -ForegroundColor Cyan

# Check if MQTT broker is reachable
$mqttHost = $env:HUAWEI_MQTT_HOST
$mqttPort = $env:HUAWEI_MQTT_PORT
try {
    $connection = Test-NetConnection -ComputerName $mqttHost -Port $mqttPort -WarningAction SilentlyContinue
    if (!$connection.TcpTestSucceeded) {
        Write-Host "⚠️  MQTT Broker not reachable at ${mqttHost}:${mqttPort}" -ForegroundColor Yellow
        Write-Host "   Make sure Mosquitto is running!" -ForegroundColor Yellow
    }
    else {
        Write-Host "✅ MQTT Broker reachable" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️  Cannot test MQTT connection" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ">> Starting Python application..." -ForegroundColor Blue
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Run - wechsle ins Addon-Verzeichnis und starte
$addonDir = Join-Path $rootDir "huawei_solar_modbus_mqtt"
Set-Location $addonDir
python -m bridge.main
