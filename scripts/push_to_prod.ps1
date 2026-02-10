# scripts/push_to_prod.ps1
# Filtered push from Dev to Prod repository with README renaming

param(
    [Parameter(Mandatory = $false)]
    [string]$TargetBranch = "dev",
    
    [Parameter(Mandatory = $false)]
    [switch]$DryRun,
    
    [Parameter(Mandatory = $false)]
    [string]$Message
)

$ProdRemote = "prod"
$ColorInfo = "Cyan"
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"

# ===== FILES/FOLDERS TO EXCLUDE FROM PROD =====
$DevOnlyFiles = @(
    # Development Scripts
    "scripts/test_addon_update.ps1",
    "scripts/push_to_prod.ps1",
    
    # Personal Development Content
    "notes",
    "en",
    "examples",
    
    # Dev README
    "README.md",
    
    # Internal Documentation
    "RELEASE_CHECKLIST.md",
    
    # IDE/Editor Config
    ".pre-commit-config.yaml",
    "pyrightconfig.json",
    ".vscode",
    ".idea",
    
    # Development Config Files
    ".env.example",
    ".shellcheckrc",
    
    # Local artifacts
    ".coverage",
    "htmlcov",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__"
)

# ===== FILES TO RENAME FOR PROD =====
$FilesToRename = @{
    "README-PRODUCTION.md"    = "README.md"
    "README.de-PRODUCTION.md" = "README.de.md"
}

# ===== VALIDATION =====
Write-Host "`n🔍 Validating..." -ForegroundColor $ColorInfo

if (-not (Test-Path ".git")) {
    Write-Host "❌ Not a git repository!" -ForegroundColor $ColorError
    exit 1
}

$remotes = git remote
if ($remotes -notcontains $ProdRemote) {
    Write-Host "❌ Remote '$ProdRemote' not found!" -ForegroundColor $ColorError
    Write-Host "   Run: git remote add $ProdRemote https://github.com/arboeh/huABus.git" -ForegroundColor $ColorWarning
    exit 1
}

$status = git status --porcelain
if ($status) {
    Write-Host "❌ Uncommitted changes detected!" -ForegroundColor $ColorError
    Write-Host "   Commit or stash changes first." -ForegroundColor $ColorWarning
    git status --short
    exit 1
}

$currentBranch = git branch --show-current

Write-Host "✅ Repository valid" -ForegroundColor $ColorSuccess
Write-Host "📦 Source: $currentBranch" -ForegroundColor $ColorInfo
Write-Host "🎯 Target: $ProdRemote/$TargetBranch`n" -ForegroundColor $ColorInfo

# ===== SHOW WHAT WILL BE EXCLUDED =====
Write-Host "❌ Excluding dev-only files:" -ForegroundColor $ColorWarning
$excludedCount = 0
foreach ($file in $DevOnlyFiles) {
    if (Test-Path $file) {
        Write-Host "   - $file" -ForegroundColor DarkGray
        $excludedCount++
    }
}

if ($excludedCount -eq 0) {
    Write-Host "   (none found)" -ForegroundColor DarkGray
}

# ===== SHOW WHAT WILL BE RENAMED =====
Write-Host "`n🔄 Files to rename:" -ForegroundColor $ColorInfo
foreach ($source in $FilesToRename.Keys) {
    $target = $FilesToRename[$source]
    if (Test-Path $source) {
        Write-Host "   $source → $target" -ForegroundColor Cyan
    }
    else {
        Write-Host "   ⚠️  $source not found (skipping)" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ Files included in push:" -ForegroundColor $ColorInfo
Write-Host "   - tests/ (needed for CI)" -ForegroundColor DarkGray
Write-Host "   - scripts/run_local.ps1 (for prod testing)" -ForegroundColor DarkGray
Write-Host "   - .github/workflows/ (CI/CD)" -ForegroundColor DarkGray
Write-Host "   - All production code" -ForegroundColor DarkGray

# ===== DRY RUN =====
if ($DryRun) {
    Write-Host "`n[DRY RUN] Would push to $ProdRemote/$TargetBranch" -ForegroundColor $ColorWarning
    
    $allFiles = git ls-files
    $includedFiles = $allFiles | Where-Object {
        $file = $_
        $exclude = $false
        foreach ($pattern in $DevOnlyFiles) {
            $patternRegex = "^" + [regex]::Escape($pattern).Replace("\*", ".*")
            if ($file -match $patternRegex) {
                $exclude = $true
                break
            }
        }
        -not $exclude
    }
    
    Write-Host "`nStatistics:" -ForegroundColor $ColorInfo
    Write-Host "   Total files: $($allFiles.Count)" -ForegroundColor White
    Write-Host "   Excluded: $excludedCount" -ForegroundColor White
    Write-Host "   Renamed: $($FilesToRename.Count)" -ForegroundColor White
    Write-Host "   Included: $($includedFiles.Count)" -ForegroundColor White
    
    exit 0
}

# ===== CONFIRMATION =====
Write-Host "`n⚠️  Ready to push to $ProdRemote/$TargetBranch" -ForegroundColor $ColorWarning
if (-not $Message) {
    $Message = Read-Host "Commit message (or ENTER for default)"
    if (-not $Message) {
        $Message = "sync: update from dev ($currentBranch)"
    }
}

Write-Host "Message: '$Message'" -ForegroundColor White
$confirm = Read-Host "`nContinue? (y/n)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "❌ Aborted" -ForegroundColor $ColorWarning
    exit 0
}

# ===== CREATE TEMPORARY BRANCH =====
$tempBranch = "temp-prod-export-$(Get-Date -Format 'yyyyMMddHHmmss')"
Write-Host "`n🔧 Creating temporary branch: $tempBranch" -ForegroundColor $ColorInfo

git checkout -b $tempBranch 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create temp branch!" -ForegroundColor $ColorError
    exit 1
}

# ===== REMOVE DEV-ONLY FILES =====
Write-Host "🧹 Removing dev-only files..." -ForegroundColor $ColorInfo

$removedCount = 0
foreach ($file in $DevOnlyFiles) {
    if (Test-Path $file) {
        git rm -r --cached $file 2>$null
        if ($LASTEXITCODE -eq 0) {
            $removedCount++
            Write-Host "   Removed: $file" -ForegroundColor DarkGray
        }
    }
}

if ($removedCount -eq 0) {
    Write-Host "   No files to remove" -ForegroundColor DarkGray
}

# ===== RENAME FILES FOR PROD =====
Write-Host "`n🔄 Renaming files for production..." -ForegroundColor $ColorInfo

$renamedCount = 0
foreach ($source in $FilesToRename.Keys) {
    $target = $FilesToRename[$source]
    
    if (Test-Path $source) {
        # Git mv zum Umbenennen
        git mv $source $target 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            $renamedCount++
            Write-Host "   Renamed: $source → $target" -ForegroundColor Cyan
        }
        else {
            Write-Host "   ⚠️  Failed to rename: $source" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "   ⚠️  Not found: $source" -ForegroundColor Yellow
    }
}

if ($renamedCount -eq 0) {
    Write-Host "   No files renamed" -ForegroundColor DarkGray
}

# ===== COMMIT CHANGES =====
Write-Host "`n💾 Committing changes..." -ForegroundColor $ColorInfo
git add -A 2>$null
git commit -m "chore: $Message" --allow-empty 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Commit failed!" -ForegroundColor $ColorError
    git checkout $currentBranch
    git branch -D $tempBranch 2>$null
    exit 1
}

# ===== PUSH TO PROD =====
Write-Host "🚀 Pushing to $ProdRemote/$TargetBranch..." -ForegroundColor $ColorInfo
git push $ProdRemote "$tempBranch`:$TargetBranch" --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Successfully pushed to $ProdRemote/$TargetBranch!" -ForegroundColor $ColorSuccess
}
else {
    Write-Host "`n❌ Push failed!" -ForegroundColor $ColorError
    git checkout $currentBranch
    git branch -D $tempBranch
    exit 1
}

# ===== CLEANUP =====
Write-Host "🧹 Cleaning up..." -ForegroundColor $ColorInfo
git checkout $currentBranch 2>$null
git branch -D $tempBranch 2>$null

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorSuccess
Write-Host "║                                                          ║" -ForegroundColor $ColorSuccess
Write-Host "║              ✅ PUSH TO PROD SUCCESSFUL! ✅              ║" -ForegroundColor $ColorSuccess
Write-Host "║                                                          ║" -ForegroundColor $ColorSuccess
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorSuccess

Write-Host "`nWhat was pushed to Prod:" -ForegroundColor $ColorInfo
Write-Host "   ✓ Production code (huawei_solar_modbus_mqtt/)" -ForegroundColor Green
Write-Host "   ✓ Tests (for CI/CD)" -ForegroundColor Green
Write-Host "   ✓ README.md (from README-PRODUCTION.md)" -ForegroundColor Green
Write-Host "   ✓ README.de.md (from README.de-PRODUCTION.md)" -ForegroundColor Green
Write-Host "   ✓ Scripts (run_local.ps1, check_version_sync.py)" -ForegroundColor Green
Write-Host "   ✓ GitHub Workflows (CI/CD pipeline)" -ForegroundColor Green

Write-Host "`nWhat stayed in Dev-only:" -ForegroundColor $ColorWarning
Write-Host "   - README.md (Dev version)" -ForegroundColor DarkGray
foreach ($file in $DevOnlyFiles) {
    if (Test-Path $file) {
        Write-Host "   - $file" -ForegroundColor DarkGray
    }
}

Write-Host "`nNext steps:" -ForegroundColor $ColorInfo
Write-Host "1. cd ..\huABus && git checkout $TargetBranch && git pull" -ForegroundColor White
Write-Host "2. .\scripts\run_local.ps1 -Test  # Run tests" -ForegroundColor White
Write-Host "3. git push origin $TargetBranch  # Push to GitHub (triggers CI)`n" -ForegroundColor White
