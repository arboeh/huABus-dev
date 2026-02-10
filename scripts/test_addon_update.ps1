# test_addon_update.ps1
# Automated Home Assistant Addon Update Testing

param(
    [string]$ProdRepo = "I:\Development\huABus",
    [string]$DevRepo = "I:\Development\huABus-dev"
)

# Farben für Output
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"
$ColorInfo = "Cyan"

function Write-Step {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor $ColorInfo
    Write-Host "  $Message" -ForegroundColor $ColorInfo
    Write-Host "========================================`n" -ForegroundColor $ColorInfo
}

function Confirm-Step {
    param([string]$Message)
    Write-Host "`n$Message" -ForegroundColor $ColorWarning
    $response = Read-Host "Fortfahren? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "❌ Abgebrochen durch Benutzer" -ForegroundColor $ColorError
        exit 1
    }
}

function Test-GitRepo {
    param([string]$Path)
    if (-not (Test-Path "$Path\.git")) {
        Write-Host "❌ Kein Git-Repository gefunden: $Path" -ForegroundColor $ColorError
        exit 1
    }
}

# ===== SCRIPT START =====
Write-Host @"

╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     Home Assistant Addon Update Test Automation          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

"@ -ForegroundColor $ColorInfo

Write-Host "Prod-Repo: $ProdRepo" -ForegroundColor White
Write-Host "Dev-Repo:  $DevRepo`n" -ForegroundColor White

# ===== VALIDIERUNG =====
Write-Step "STEP 0: Validierung"

Test-GitRepo -Path $ProdRepo
Test-GitRepo -Path $DevRepo

Write-Host "✅ Prod-Repo gefunden" -ForegroundColor $ColorSuccess
Write-Host "✅ Dev-Repo gefunden" -ForegroundColor $ColorSuccess

# Prüfe uncommitted changes
Push-Location $DevRepo
$status = git status --porcelain
if ($status) {
    Write-Host "`n⚠️  Uncommitted changes im Dev-Repo gefunden:" -ForegroundColor $ColorWarning
    git status --short
    Confirm-Step "Trotzdem fortfahren?"
}
Pop-Location

Confirm-Step "Bereit für Update-Test?"

# ===== STEP 1: BACKUP =====
Write-Step "STEP 1: Backup erstellen"

Push-Location $DevRepo
$backupBranch = "backup-updatetest-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host "Erstelle Backup-Branch: $backupBranch" -ForegroundColor White
git branch $backupBranch

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backup erstellt: $backupBranch" -ForegroundColor $ColorSuccess
    git branch | Select-String "backup-updatetest"
}
else {
    Write-Host "❌ Backup fehlgeschlagen!" -ForegroundColor $ColorError
    Pop-Location
    exit 1
}
Pop-Location

Confirm-Step "Backup erfolgreich. Weiter zu Phase 1 (Install v1.7.4)?"

# ===== STEP 2: PUSH v1.7.4 =====
Write-Step "STEP 2: Push v1.7.4 zu Dev-Repo"

Push-Location $ProdRepo

# Prüfe ob 'dev' remote existiert
$remotes = git remote
if ($remotes -notcontains "dev") {
    Write-Host "Remote 'dev' nicht gefunden. Füge hinzu..." -ForegroundColor $ColorWarning
    git remote add dev https://github.com/arboeh/huABus-dev.git
    Write-Host "✅ Remote 'dev' hinzugefügt" -ForegroundColor $ColorSuccess
}

Write-Host "Wechsel zu main Branch..." -ForegroundColor White
git checkout main

Write-Host "Push Prod/main (v1.7.4) → Dev/main..." -ForegroundColor White
git push dev main:main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ v1.7.4 erfolgreich gepusht" -ForegroundColor $ColorSuccess
}
else {
    Write-Host "❌ Push fehlgeschlagen!" -ForegroundColor $ColorError
    Pop-Location
    exit 1
}
Pop-Location

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $ColorWarning
Write-Host "  📋 AUFGABE: Home Assistant Installation" -ForegroundColor $ColorWarning
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $ColorWarning
Write-Host "1. Supervisor → Add-on Store → ⋮ → Repositories" -ForegroundColor White
Write-Host "2. Repository hinzufügen: https://github.com/arboeh/huABus-dev" -ForegroundColor White
Write-Host "3. Addon 'huABus' installieren (sollte v1.7.4 sein)" -ForegroundColor White
Write-Host "4. Konfigurieren & Starten" -ForegroundColor White
Write-Host "5. Testen ob alles funktioniert" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor $ColorWarning

Confirm-Step "Installation & Test abgeschlossen? Weiter zu Phase 2 (Update v1.8.0)?"

# ===== STEP 3: PUSH v1.8.0 =====
Write-Step "STEP 3: Push v1.8.0 zu Dev-Repo"

Push-Location $ProdRepo

Write-Host "Wechsel zu dev Branch..." -ForegroundColor White
git checkout dev

Write-Host "Push Prod/dev (v1.8.0) → Dev/main..." -ForegroundColor White
git push dev dev:main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ v1.8.0 erfolgreich gepusht" -ForegroundColor $ColorSuccess
}
else {
    Write-Host "❌ Push fehlgeschlagen!" -ForegroundColor $ColorError
    Pop-Location
    exit 1
}
Pop-Location

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $ColorWarning
Write-Host "  📋 AUFGABE: Home Assistant Update" -ForegroundColor $ColorWarning
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $ColorWarning
Write-Host "1. Supervisor → Add-on Store → ↻ Reload" -ForegroundColor White
Write-Host "2. Zu 'huABus' Addon navigieren" -ForegroundColor White
Write-Host "3. 'Update' Button klicken (1.7.4 → 1.8.0)" -ForegroundColor White
Write-Host "4. Log beobachten während Update" -ForegroundColor White
Write-Host "5. Prüfen:" -ForegroundColor White
Write-Host "   - Config-Werte erhalten?" -ForegroundColor White
Write-Host "   - Neue Option 'Auto-detect Slave ID' sichtbar?" -ForegroundColor White
Write-Host "   - Register-Count dynamisch?" -ForegroundColor White
Write-Host "   - Addon startet erfolgreich?" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor $ColorWarning

Confirm-Step "Update-Test abgeschlossen? Weiter zu Restore?"

# ===== STEP 4: RESTORE =====
Write-Step "STEP 4: Dev-Repo wiederherstellen"

Push-Location $DevRepo

Write-Host "Wechsel zu Backup-Branch: $backupBranch" -ForegroundColor White
git checkout $backupBranch

Write-Host "Lösche alten main Branch..." -ForegroundColor White
git branch -D main

Write-Host "Erstelle neuen main aus Backup..." -ForegroundColor White
git checkout -b main

Write-Host "Push zu origin..." -ForegroundColor White
git push origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dev-Repo erfolgreich wiederhergestellt" -ForegroundColor $ColorSuccess
}
else {
    Write-Host "❌ Restore fehlgeschlagen!" -ForegroundColor $ColorError
    Write-Host "⚠️  Backup-Branch '$backupBranch' existiert noch!" -ForegroundColor $ColorWarning
    Pop-Location
    exit 1
}

# Verifizierung
Write-Host "`nVerifizierung:" -ForegroundColor $ColorInfo
git log --oneline -5

Pop-Location

Confirm-Step "Restore erfolgreich. Backup-Branch löschen?"

# ===== STEP 5: CLEANUP =====
Write-Step "STEP 5: Cleanup"

Push-Location $DevRepo

Write-Host "Lösche Backup-Branch: $backupBranch" -ForegroundColor White
git branch -D $backupBranch

Write-Host "✅ Backup-Branch gelöscht" -ForegroundColor $ColorSuccess

Write-Host "`nVerbleibende Backup-Branches:" -ForegroundColor $ColorInfo
$backups = git branch | Select-String "backup-updatetest"
if ($backups) {
    $backups
}
else {
    Write-Host "  (keine)" -ForegroundColor DarkGray
}

Pop-Location

# ===== FERTIG =====
Write-Host "`n" -NoNewline
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorSuccess
Write-Host "║                                                          ║" -ForegroundColor $ColorSuccess
Write-Host "║              ✅ UPDATE-TEST ABGESCHLOSSEN! ✅           ║" -ForegroundColor $ColorSuccess
Write-Host "║                                                          ║" -ForegroundColor $ColorSuccess
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorSuccess

Write-Host "`nDev-Repo ist wieder im Original-Zustand." -ForegroundColor White
Write-Host "Du kannst jetzt normal weiterentwickeln.`n" -ForegroundColor White
