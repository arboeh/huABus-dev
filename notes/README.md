# Release Checklist

Interne Anleitung zum Erstellen einer neuen Version des Huawei Solar Modbus MQTT Add-ons.

## Repository-Setup

### Development & Production Struktur

```
I:\Development\
├── huABus-dev/          # 🔧 Development Repo (main branch)
│   ├── Remote: origin   # → GitHub arboeh/huABus-dev
│   └── Remote: prod     # → GitHub arboeh/huABus
│
└── huABus/              # 🌞 Production Repo (main + dev branches)
    └── Remote: origin   # → GitHub arboeh/huABus
```

**Workflow:**

1. Development in `huABus-dev` (main branch)
2. Push zu `huABus` (dev branch) für Testing - **automatisch gefiltert**
3. Merge dev → main für Release

**Dev-Only Files (werden automatisch ausgefiltert):**
- `notes/` - Persönliche Notizen
- `en/` - Work-in-Progress Übersetzungen
- `RELEASE_CHECKLIST.md` - Diese Datei
- `scripts/test_addon_update.ps1` - Update-Testing Script
- `scripts/push_to_prod.ps1` - Push-Script selbst
- `README.md` - Dev-README (wird durch README-PRODUCTION.md ersetzt)
- IDE Config (`.vscode/`, `.idea/`, `.pre-commit-config.yaml`, etc.)

---

## Voraussetzungen

- [ ] Virtual Environment vorhanden (`venv` oder `.venv`)
- [ ] Pre-commit Hooks installiert (`pre-commit install`) - **nur im Dev-Repo**
- [ ] Python 3.11+
- [ ] Remote `prod` konfiguriert im dev-repo
- [ ] Alle Änderungen committed

### Remote Setup (einmalig)

```powershell
# Im Development Repo
cd I:\Development\huABus-dev
git remote add prod https://github.com/arboeh/huABus.git

# Verify
git remote -v
# Sollte zeigen:
# origin  https://github.com/arboeh/huABus-dev.git
# prod    https://github.com/arboeh/huABus.git
```

---

## Release Workflow

### 1. Development abschließen (in huABus-dev)

```powershell
cd I:\Development\huABus-dev

# Virtual Environment aktivieren
.\venv\Scripts\Activate.ps1
```

**Erwartete Ausgabe:** Prompt zeigt `(venv)` Prefix

---

### 2. Pre-commit Hooks ausführen

```bash
# Alle Dateien prüfen (empfohlen vor Release)
pre-commit run --all-files
```

**Prüft automatisch:**

- ✅ Ruff Check - Code-Qualität (Linting)
- ✅ Ruff Format - Code-Style (Formatting)
- ✅ MyPy - Type Checking
- ✅ Trailing Whitespace - Leerzeichen am Zeilenende
- ✅ End of Files - Newline am Dateiende
- ✅ YAML Syntax - config.yaml Validierung
- ✅ Large Files - Verhindert versehentliches Commit großer Dateien
- ✅ Merge Conflicts - Prüft auf vergessene Conflict-Marker
- ✅ TOML Syntax - pyproject.toml Validierung
- ✅ Line Endings - Konsistente Zeilenenden (LF/CRLF)
- ✅ Version Sync - Prüft config.yaml ↔ __version__.py

**Bei Fehlern:**

```bash
# Automatisches Fixing
pre-commit run --all-files

# Nach Fixes erneut prüfen
pre-commit run --all-files
```

---

### 3. Version aktualisieren

#### Single Source of Truth

**Datei:** `huawei_solar_modbus_mqtt/config.yaml`

```yaml
version: '1.8.0' # Neue Version hier eintragen
```

#### Automatische Synchronisation

```bash
python scripts/update_version.py
```

**Aktualisiert automatisch:**

1. `huawei_solar_modbus_mqtt/bridge/__version__.py` → `__version__ = "1.8.0"`
2. Dependency-Versionen in `requirements.txt` (falls geändert)

---

### 4. Tests ausführen

```powershell
# Alle Tests mit Coverage-Report
.\scripts\run_local.ps1 -Test -Coverage
```

**Erwartung:**

- ✅ Alle Tests bestehen
- ✅ Coverage ≥ 85%

---

### 5. CHANGELOG.md aktualisieren

**Format:** [Keep a Changelog](https://keepachangelog.com/)

```markdown
## [1.8.0] - 2026-02-09

### Added

- Automatic Slave ID detection (tries 0, 1, 100)
- New config option: `modbus_auto_detect_slave_id`
- UI toggle for auto-detection in add-on configuration
- Dynamic register count display in startup logs

### Changed

- MQTT authentication now uses Home Assistant credentials by default
- Improved error handling for Modbus connection failures

### Fixed

- Heartbeat timeout bei langen Modbus-Reads (#42)
```

---

### 6. Production READMEs aktualisieren

**User-facing Dokumentation bearbeiten:**

```powershell
# Englische Version (für GitHub arboeh/huABus)
code README-PRODUCTION.md

# Deutsche Version
code README.de-PRODUCTION.md
```

**Hinweis:** Diese werden beim Push automatisch zu `README.md` und `README.de.md` im Prod-Repo umbenannt.

---

### 7. Commit im dev-Repo

```bash
cd I:\Development\huABus-dev

# Pre-commit Hook läuft automatisch
git add .
git commit -m "chore: bump version to 1.8.0"
git push origin main

# Verify
git log --oneline -3
```

---

### 8. Push zu Production/dev (Automatisch gefiltert)

```powershell
cd I:\Development\huABus-dev

# Optional: Dry-Run zum Testen
.\scripts\push_to_prod.ps1 -DryRun

# Gefilterter Push zu Prod/dev
.\scripts\push_to_prod.ps1
```

**Das Script macht automatisch:**

1. ✅ Entfernt dev-only Files (`notes/`, `RELEASE_CHECKLIST.md`, etc.)
2. ✅ Benennt `README-PRODUCTION.md` → `README.md` um
3. ✅ Benennt `README.de-PRODUCTION.md` → `README.de.md` um
4. ✅ Behält Tests & Production Code
5. ✅ Pusht zu `prod/dev` Branch

**Erwartete Ausgabe:**

```
✅ Successfully pushed to prod/dev!

What was pushed to Prod:
   ✓ Production code (huawei_solar_modbus_mqtt/)
   ✓ Tests (for CI/CD)
   ✓ README.md (from README-PRODUCTION.md)
   ✓ README.de.md (from README.de-PRODUCTION.md)
   ...

What stayed in Dev-only:
   - notes/
   - RELEASE_CHECKLIST.md
   - scripts/test_addon_update.ps1
   - scripts/push_to_prod.ps1
```

---

### 9. Update-Testing (Realitätsnah)

#### Automatisiertes Testing mit Script

```powershell
cd I:\Development\huABus-dev\scripts
.\test_addon_update.ps1
```

**Das Script:**

1. ✅ Erstellt automatisch Backup vom Dev-Repo
2. ✅ Pusht alte Version (Prod/main) → Dev/main
3. ⏸️ Pausiert für Installation in Home Assistant
4. ✅ Pusht neue Version (Prod/dev) → Dev/main
5. ⏸️ Pausiert für Update-Test in Home Assistant
6. ✅ Stellt Dev-Repo automatisch wieder her
7. ✅ Löscht Backup-Branch

**In Home Assistant prüfen:**

- [ ] Config-Werte erhalten?
- [ ] Neue Features sichtbar?
- [ ] Addon startet erfolgreich?

---

### 10. CI Testing & Final Checks

```bash
cd I:\Development\huABus

# Dev branch zu GitHub pushen (CI läuft)
git checkout dev
git pull
git push origin dev
```

**Warte auf CI:**

- [GitHub Actions](https://github.com/arboeh/huABus/actions)
- Alle Tests müssen grün sein ✅

**Optional: Lokaler Test**

```powershell
# Im Production Repo auf dev branch
cd I:\Development\huABus
git checkout dev

# Test-Run
.\scripts\run_local.ps1 -Test
```

---

### 11. Release erstellen (Production)

```bash
cd I:\Development\huABus

# Merge dev → main
git checkout main
git merge dev --no-ff -m "Release v1.8.0: Auto Slave ID Detection"

# Git Tag erstellen
git tag -a v1.8.0 -m "Release v1.8.0

### Added
- Automatic Slave ID detection
- MQTT auto-authentication
- Dynamic register count

### Changed
- Improved error handling

### Fixed
- Connection timeout issues"

# Push zu GitHub (löst Release-Build aus)
git push origin main --tags
git push origin dev
```

**Commit-Message-Format:**

- Release: `Release v1.8.0: Feature-Name`
- Hotfix: `Hotfix v1.8.0.1`
- Pre-Release: `Pre-release v1.9.0-beta.1`

---

### 12. GitHub Release (Automatisch)

Nach dem Push mit Tag:

1. **GitHub Actions** startet automatisch
2. **Build** für alle Architekturen (amd64, armhf, armv7, aarch64, i386)
3. **Docker Images** werden zu GitHub Container Registry gepusht
4. **Release-Notes** aus `CHANGELOG.md` werden extrahiert

**Fortschritt prüfen:**

- [GitHub Actions](https://github.com/arboeh/huABus/actions)
- Workflow: "Build and Publish"

**Erwartete Dauer:** 15-25 Minuten (alle Architekturen)

---

### 13. Weiterentwicklung (zurück zu dev-repo)

```bash
cd I:\Development\huABus-dev

# Einfach weiter entwickeln auf main!
git checkout main

# Neue Features für v1.9.0
git add .
git commit -m "feat: new awesome feature"
```

**Dein dev-repo/main bleibt unberührt und ist deine Development-Umgebung!**

---

## Troubleshooting

### Push zu prod-repo schlägt fehl

**Symptom:** `Remote 'prod' not found`

```powershell
cd I:\Development\huABus-dev

# Remote hinzufügen
git remote add prod https://github.com/arboeh/huABus.git

# Erneut versuchen
.\scripts\push_to_prod.ps1
```

### CI läuft nicht an

**Ursache:** Nur lokal gepusht, nicht zu GitHub

```bash
cd I:\Development\huABus

# Push zu origin (GitHub)
git checkout dev
git push origin dev
```

### Version nicht synchron

```bash
cd I:\Development\huABus-dev

# Erneut synchronisieren
python scripts/update_version.py

# Pre-commit prüft automatisch
pre-commit run check-version-sync --all-files
```

### Pre-commit Hook schlägt fehl

```bash
# Hooks neu installieren
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### Update-Test: Dev-Repo wiederherstellen fehlgeschlagen

```powershell
cd I:\Development\huABus-dev

# Finde Backup-Branch
git branch -a | Select-String "backup-updatetest"

# Manuell wiederherstellen
git checkout backup-updatetest-XXXXXX
git branch -D main
git checkout -b main
git push origin main --force
```

### Update-Test: Lock-Datei verhindert Checkout

```powershell
cd I:\Development\huABus-dev

# Git-Prozesse beenden
Get-Process git* | Stop-Process -Force

# Lock-Datei löschen
Remove-Item .git\index.lock -Force

# Erneut versuchen
git checkout backup-updatetest-XXXXXX
```

### Push-Script: Uncommitted changes

```powershell
# Änderungen committen
git add .
git commit -m "wip: current work"

# Oder stashen
git stash

# Dann erneut pushen
.\scripts\push_to_prod.ps1
```

---

## Post-Release

### 1. Release-Notes verifizieren

- [ ] [GitHub Releases](https://github.com/arboeh/huABus/releases) prüfen
- [ ] Changelog korrekt übernommen
- [ ] Alle Assets vorhanden (Docker Images)

### 2. Community informieren

- [ ] Home Assistant Community Forum Post aktualisieren
- [ ] GitHub Discussions (Announcement)
- [ ] Issue-Tracker: Relevante Issues schließen mit "Fixed in v1.8.0"

### 3. Beta-Tester benachrichtigen

```markdown
🎉 **v1.8.0 ist live!**

Danke an alle Beta-Tester! Die Auto Slave ID Detection ist jetzt verfügbar.

Update via Home Assistant: Add-on → Check for Updates
```

---

## Checkliste vor Release

Kopiere diese Liste in GitHub Issue oder PR:

```markdown
## Release v1.8.0 Checklist

### Development (huABus-dev)

- [ ] Virtual Environment aktiviert
- [ ] Pre-commit Hooks erfolgreich (`pre-commit run --all-files`)
- [ ] Version in `config.yaml` aktualisiert (1.8.0)
- [ ] `update_version.py` ausgeführt
- [ ] Alle Tests bestehen (✅)
- [ ] Coverage ≥ 85%
- [ ] CHANGELOG.md aktualisiert
- [ ] README-PRODUCTION.md aktualisiert
- [ ] README.de-PRODUCTION.md aktualisiert
- [ ] Commit erstellt: `chore: bump version to 1.8.0`
- [ ] Push zu GitHub: `git push origin main`
- [ ] Push zu prod: `.\scripts\push_to_prod.ps1`

### Update Testing

- [ ] Backup erstellt (automatisch via Script)
- [ ] Alte Version in HA installiert & getestet
- [ ] Update durchgeführt & getestet
- [ ] Config-Werte erhalten
- [ ] Neue Features sichtbar
- [ ] Dev-Repo wiederhergestellt

### Testing (huABus/dev)

- [ ] Push zu GitHub: `git push origin dev`
- [ ] GitHub Actions erfolgreich (alle Tests grün)
- [ ] Lokaler Test erfolgreich (optional)

### Release (huABus/main)

- [ ] Merge dev → main: `git merge dev --no-ff`
- [ ] Git Tag erstellt: `v1.8.0`
- [ ] Push zu GitHub: `git push origin main --tags`
- [ ] GitHub Actions Build erfolgreich (alle Architekturen)
- [ ] Release-Notes verifiziert

### Post-Release

- [ ] Docker Images verfügbar
- [ ] Community informiert
- [ ] Beta-Tester benachrichtigt
- [ ] Relevante Issues geschlossen
```

---

## Semantic Versioning

Dieses Projekt folgt [SemVer 2.0.0](https://semver.org/):

- **MAJOR** (1.x.x): Breaking Changes, API-Änderungen
- **MINOR** (x.8.x): Neue Features, abwärtskompatibel
- **PATCH** (x.x.1): Bugfixes, keine neuen Features

**Beispiele:**

- `1.8.0` → `1.8.1`: Bugfix (Auto-detect Timeout gefixt)
- `1.8.0` → `1.9.0`: Neues Feature (Web-UI für Konfiguration)
- `1.8.0` → `2.0.0`: Breaking Change (Config-Format YAML → TOML)

---

## Quick Reference

### Tägliche Development

```powershell
cd I:\Development\huABus-dev
# ... develop, test, commit ...
git push origin main
```

### Push zu Production (gefiltert)

```powershell
cd I:\Development\huABus-dev

# Dry-Run (zeigt was passiert)
.\scripts\push_to_prod.ps1 -DryRun

# Echter Push
.\scripts\push_to_prod.ps1

# Mit custom Message
.\scripts\push_to_prod.ps1 -Message "Add feature X"

# Direct zu main (Hotfix)
.\scripts\push_to_prod.ps1 -TargetBranch main
```

### Update Testing (Automatisch)

```powershell
cd I:\Development\huABus-dev\scripts
.\test_addon_update.ps1
# Script führt durch den kompletten Test-Zyklus
```

### Release

```powershell
cd I:\Development\huABus
git checkout main
git merge dev --no-ff -m "Release v1.X.Y"
git tag v1.X.Y
git push origin main --tags
```

### Back to Development

```powershell
cd I:\Development\huABus-dev
# Einfach weiter entwickeln!
```

---

## Scripts

### push_to_prod.ps1

Automatisierter, gefilterter Push vom Dev-Repo zum Prod-Repo.

**Location:** `I:\Development\huABus-dev\scripts\push_to_prod.ps1`

**Features:**

- ✅ Automatisches Filtern von dev-only Files
- ✅ README-Umbenennung (README-PRODUCTION.md → README.md)
- ✅ Validierung (uncommitted changes, remotes)
- ✅ Dry-Run Modus
- ✅ Interaktive Bestätigung
- ✅ Farbiges Output

**Usage:**

```powershell
# Standard (pusht zu prod/dev)
.\scripts\push_to_prod.ps1

# Dry-Run
.\scripts\push_to_prod.ps1 -DryRun

# Mit Message
.\scripts\push_to_prod.ps1 -Message "Add auto-detect feature"

# Zu anderem Branch
.\scripts\push_to_prod.ps1 -TargetBranch main
```

**Was wird gefiltert:**

- `notes/`, `en/` - Persönliche Notizen
- `RELEASE_CHECKLIST.md` - Interne Doku
- `scripts/test_addon_update.ps1` - Dev-Script
- `scripts/push_to_prod.ps1` - Das Script selbst
- `README.md` - Dev-README
- IDE Config (`.vscode/`, `.pre-commit-config.yaml`, etc.)

**Was wird umbenannt:**

- `README-PRODUCTION.md` → `README.md`
- `README.de-PRODUCTION.md` → `README.de.md`

**Was bleibt:**

- `tests/` - Für CI/CD
- `scripts/run_local.ps1` - Testing
- Production Code
- GitHub Workflows

---

### test_addon_update.ps1

Automatisiertes Update-Testing für realitätsnahe Simulation des User-Update-Flows.

**Location:** `I:\Development\huABus-dev\scripts\test_addon_update.ps1`

**Features:**

- ✅ Automatisches Backup & Restore
- ✅ Dynamische Versionserkennung aus `config.yaml`
- ✅ Interaktive Bestätigung für jeden Schritt
- ✅ Fehlerbehandlung mit Rollback-Info
- ✅ Farbiges Output für bessere Übersicht

**Usage:**

```powershell
# Standard (mit Default-Pfaden)
.\scripts\test_addon_update.ps1

# Mit custom Pfaden
.\scripts\test_addon_update.ps1 -ProdRepo "C:\Projekte\huABus" -DevRepo "C:\Projekte\huABus-dev"
```

**Ablauf:**

1. Validierung (Repos vorhanden, uncommitted changes)
2. Backup erstellen (automatisch benannter Branch)
3. Alte Version pushen → HA Installation testen
4. Neue Version pushen → HA Update testen
5. Dev-Repo wiederherstellen
6. Cleanup (Backup-Branch löschen)

---

## 🎯 Key Takeaways

1. **Two-Repo-Setup** - Dev für Entwicklung, Prod für Testing & Release
2. **Automatisches Filtern** - `push_to_prod.ps1` entfernt dev-only Files
3. **README-Management** - Production-READMEs im Dev-Repo bearbeiten
4. **Update-Testing** - Immer vor Release mit realem HA-Flow testen
5. **Automatisierung** - Scripts für wiederkehrende Tasks nutzen
6. **Version Sync** - Immer via `update_version.py` synchronisieren
7. **CI-Trigger** - Nur bei Push zu GitHub, nicht lokal
8. **Backup wichtig** - Vor Update-Tests immer Backup erstellen
9. **Pre-commit nur in Dev** - Prod-Repo braucht keine Hooks
