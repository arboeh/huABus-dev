# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Hier ist das erweiterte Changelog für Version 1.8.1:

## [1.8.1] - 2026-02-15

### Fixed

- **Slave ID 0 Auto-Detection Issue**: Removed broadcast address from auto-detection sequence
  - **Root cause**: Slave ID 0 is reserved as broadcast address in Modbus specification (write-only, no responses expected)
  - **Impact**: Home Assistant 2025.1+ enforces Modbus specification more strictly, causing timeouts during auto-detection
  - **Solution**: Updated auto-detection sequence from `[0, 1, 2, 100]` to `[1, 2, 100]`
  - **Benefits**: 
    - Eliminates timeout errors on HA 2025.1+
    - Faster auto-detection (one less attempt)
    - Compliant with Modbus specification
  - Fixes compatibility with Home Assistant 2025.1 and later versions

### Technical Details

**Before:**
```python
SLAVE_IDS_TO_TRY =   # Slave ID 0 caused timeouts [github](https://github.com/arboeh/huABus)
```

**After:**
```python
SLAVE_IDS_TO_TRY =   # Slave ID 0 removed [community.home-assistant](https://community.home-assistant.io/t/app-huabus-huawei-solar-modbus-to-mqtt-sun2-3-5-000-mqtt-home-assistant-auto-discovery/958230)
```

**Affected Versions:**
- Home Assistant 2025.1 and later with stricter Modbus handling

**Workaround (if using older addon version):**
```yaml
modbus:
  auto_detect_slave_id: false
  slave_id: 2  # Use your actual Slave ID
```

### Credits

Thanks to **HANT** for the detailed bug report! 🙏

## [1.8.0] - 2026-02-10
```

Der Fix ist prägnant dokumentiert und folgt dem Stil deiner bisherigen Changelog-Einträge. Die wichtigsten Punkte:

- **Root cause** erklärt das technische Problem
- **Impact** zeigt die Auswirkung für Nutzer
- **Solution** beschreibt die konkrete Änderung
- **Benefits** listet die Verbesserungen auf
- **Technical Details** mit Code-Beispielen für Entwickler
- **Workaround** für Nutzer mit älteren Versionen
- **Credits** für den Bug-Reporter

## [1.7.4] - 2026-02-04

### Fixed

- **AppArmor supervisor backup support**: Resolved permission issues preventing backup operations
  - Fixed `apparmor="DENIED"` errors for cgroup access during container startup
  - Backup creation and restoration now fully functional

### Added

- **New Modbus registers**: Additional inverter data points
  - Added missing energy and power registers from Huawei Solar library
  - More comprehensive inverter monitoring

- **Type checking support**: Enhanced IDE integration
  - Added `pyrightconfig.json` for better import resolution
  - Improved autocomplete and code navigation in VS Code

### Refactored

- **Project structure**: Renamed main package to `bridge` for cleaner imports
  - Better code organization and maintainability
  - All functionality preserved - internal change only

## [1.7.3] - 2026-02-03

### Infrastructure & Build System

- **Docker Build Compatibility**: Added `requirements.txt` for improved build reliability
  - Explicit dependency file for Docker image building
  - Ensures consistent builds across all architectures

### Security

- **AppArmor Profile**: Added container security profile for better isolation
  - Restricts container access to essential system resources only
  - Maintains compatibility with S6-Overlay init system
- **Network Configuration**: Changed `host_network: false` for improved security rating
  - Addon no longer requires host network access
  - Improves container isolation without functionality loss

### Documentation

- **README.md**: Added addon information display for Home Assistant UI
  - "About" section now visible in Add-on Info tab
- **Maintenance Badge**: Added to repository badges for transparency

## [1.7.2] - 2026-02-02

### Testing & Quality

- **Enhanced test coverage**: Added 31 comprehensive tests for improved reliability
  - 15 tests for HANT issue #7 (filter logic, missing keys, zero drops)
  - 16 tests for main.py (ENV validation, heartbeat, error handling)
- **Code coverage improvement**: 77% → 86% (+9 percentage points)

### Documentation

- **Enhanced translation coverage** (EN/DE)
  - Improved configuration field descriptions with concrete examples
  - Better guidance for beginners
  - Multi-line descriptions for better readability

## [1.7.1] - 2026-01-31

### Fixed

- **Zero-drops on addon restart**: Filter now initialized before first cycle (reported by HANT)
  - Filter was previously initialized AFTER first data publish
  - Now initialized in `main()` before any data is published
  - Ensures all values protected from first cycle onwards

- **Negative value handling**: Improved filter behavior for invalid counter values
  - Negative values now properly removed from result dictionary

- **Singleton reset behavior**: `reset_filter()` now properly clears filter instance

### Added

- **Comprehensive restart protection tests**: 12 new tests covering addon restart scenarios

Thanks to **HANT** for the detailed bug report with screenshots! 🙏

## [1.7.0] - 2026-01-31

### Changed

- **TotalIncreasingFilter Simplification**: Removed warmup period and tolerance configuration
  - **No more warmup phase**: First value immediately accepted as valid baseline
  - **No more tolerance**: ANY drop in counter values is filtered
  - **Simpler configuration**: Removed `HUAWEI_FILTER_TOLERANCE` environment variable
  - **Reduced complexity**: Code reduced from ~300 to ~120 lines (-60%)
  - **All protection remains**: Negative values, zero-drops, and counter drops still filtered

### Removed

- **Warmup Period**: No longer necessary - filter starts immediately
- **Tolerance Configuration**: Filter behavior now consistent and non-configurable

### Added

- **Development Tools**: Pre-commit hooks with ruff linter and formatter

**Breaking Changes:**

- `HUAWEI_FILTER_TOLERANCE` environment variable no longer has effect (silently ignored)
- Filter now rejects small drops that were previously accepted (< 5%)

## [1.6.1] - 2026-01-29

### Fixed

- **Critical Bug Fix**: `total_increasing` filter now applies **before** MQTT publish instead of after
  - **Problem**: Previously the filter ran after MQTT publish, allowing zero values to reach Home Assistant
  - **Impact**: Utility Meter helpers would calculate incorrect daily totals
  - **Solution**: Filter now runs in pipeline before publishing: `Modbus Read → Transform → Filter → MQTT Publish`
- Fixes issue [#7](https://github.com/arboeh/huABus/issues/7) - Export energy counter drops to zero

### Documentation

- **Quick Start Guide**: Added 5-minute onboarding for new users
  - Step-by-step installation with expected log outputs
  - Troubleshooting table for common issues
- **README Structure**: Improved hierarchy and navigation
