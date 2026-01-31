# Changelog

All notable changes to this project will be documented in this file.

## [1.7.1] - 2026-01-31

### Fixed

- **Zero-drops on addon restart**: Filter now initialized before first cycle (reported by HANT)
  - Filter was previously initialized AFTER first data publish, leaving brief unprotected moment
  - Now initialized in `main()` before any data is published
  - Ensures all values protected from first cycle onwards
  - Log order after fix:
    1. 🔌 Connected (Slave ID: X)
    2. 🔍 TotalIncreasingFilter initialized (simplified)
    3. ⏱️ Poll interval: Xs
    4. 📊 Published (with filter protection) ✅

- **Negative value handling**: Improved filter behavior for invalid counter values
  - Negative values now properly removed from result dictionary
  - Fixed `_should_filter()` method to avoid side effects (no storing in check method)
  - Storing moved to `filter()` method for cleaner separation of concerns

- **Singleton reset behavior**: `reset_filter()` now properly clears filter instance
  - Previous behavior only cleared internal state but kept instance alive
  - Now fully resets singleton for clean restart
  - Next `get_filter()` call creates fresh instance

### Added

- **Comprehensive restart protection tests**: 12 new tests covering addon restart scenarios
  - Tests verify first value acceptance after restart
  - Edge cases: negative values, zero values, large jumps, multiple restarts
  - Validates no zero-drops visible in Home Assistant
  - All tests passing ✅

### Changed

- **Updated existing tests**: Refactored to use public API instead of private methods
  - Tests now use `filter()` instead of `_should_filter()`
  - Better test isolation and maintainability
  - Total test count: 51 tests passing

### Technical Details

**Fix Impact:**

- Prevents zero-drops in Home Assistant energy dashboard during addon restarts
- Eliminates brief unprotected moment between startup and first filter application
- More robust handling of edge cases (negative values, missing keys)

**Test Coverage:**

- Unit tests: 27 (filter logic, transform, error tracking)
- Integration tests: 12 (restart protection, singleton behavior)
- E2E tests: 12 (complete workflows, MQTT lifecycle)

Thanks to **HANT** for the detailed bug report with screenshots! 🙏

## [1.7.0] - 2026-01-31

### Changed

- **TotalIncreasingFilter Simplification**: Removed warmup period and tolerance configuration for more predictable behavior
  - **No more warmup phase**: First value is immediately accepted as valid baseline (no 60-second learning period)
  - **No more tolerance**: ANY drop in counter values is filtered (previously allowed 5% tolerance)
  - **Simpler configuration**: Removed `HUAWEI_FILTER_TOLERANCE` environment variable
  - **Reduced complexity**: Code reduced from ~300 to ~120 lines (-60%)
  - **All protection remains**: Negative values, zero-drops, and counter drops still filtered
  - **Improved logging**: Filter statistics now show exactly which values were filtered
  - **Result**: More strict but more predictable filtering - suitable for stable Modbus connections

### Removed

- **Warmup Period**: No longer necessary - filter starts immediately with first valid value
  - Removes 60-second startup delay
  - Removes warmup status indicators (`🔥 Warmup active`)
  - First read establishes baseline immediately
- **Tolerance Configuration**: Filter behavior now consistent and non-configurable
  - No more `HUAWEI_FILTER_TOLERANCE` environment variable
  - Previous 5% tolerance removed - all drops filtered equally
  - Eliminates configuration confusion

### Fixed

- **Test Suite**: Reduced from 72 to 48 tests (-33%)
  - Removed 15 warmup tests (`test_warmup.py` deleted)
  - Removed 9 tolerance-related tests
  - Split `test_hant_issue.py` into `test_hant_missing_keys.py` and `test_hant_zero_drops.py`
  - All remaining tests passing ✅

### Added

- **Development Tools**: Pre-commit hooks with ruff linter and formatter
  - Automatic code quality checks before each commit
  - Ensures consistent code style across project
  - Configured in `.pre-commit-config.yaml`

### Technical Details

**Filter Behavior Changes:**

Before (1.6.x):

```python
# Warmup: First 60 seconds accepted all values
# Tolerance: Drops < 5% accepted
10000 → 9510  # 4.9% drop → ACCEPTED ✅
10000 → 9490  # 5.1% drop → FILTERED ❌
```

Now (1.7.0):

```python
# No warmup: First value = baseline
# No tolerance: All drops filtered
10000 → 9999  # ANY drop → FILTERED ❌
10000 → 9510  # ANY drop → FILTERED ❌
```

**Filter Protection Still Active:**

- ✅ Negative values filtered
- ✅ Zero-drops filtered (e.g., 9799.5 → 0)
- ✅ Counter decreases filtered
- ✅ Missing keys handled (filled with last valid value)
- ✅ First value always accepted

**When to Upgrade:**

- ✅ **Stable Modbus connection**: Stricter filtering improves data quality
- ⚠️ **Unstable connection**: Monitor logs after upgrade - may need poll_interval increase

**Breaking Changes:**

- `HUAWEI_FILTER_TOLERANCE` environment variable no longer has effect (silently ignored)
- Filter now rejects small drops that were previously accepted (< 5% of previous value)
- Log messages changed:
  - Removed: `🔥 Warmup active (X/60s)` and `✅ Warmup complete`
  - Removed: `TotalIncreasingFilter initialized with X% tolerance`
  - New: Simpler `TotalIncreasingFilter initialized` message

**Migration Guide:**

1. No configuration changes needed - filter works out of the box
2. After upgrade, monitor filter summaries in logs:
   ```
   INFO - 🔍 Filter summary (last 20 cycles): X values filtered
   ```
3. If you see frequent filtering (every cycle), consider:
   - Increasing `poll_interval` from 30s to 60s
   - Checking Modbus connection stability
   - Reviewing network latency to inverter

**Upgrade Notes:**

- Existing configurations continue to work without changes
- `HUAWEI_FILTER_TOLERANCE` in config silently ignored (backward compatible)
- First cycle after upgrade establishes new baseline immediately
- No data loss - filter continues protecting energy statistics

**Hauptänderungen:**

- Code-Blöcke mit ` ```python ` für Syntax-Highlighting
- Listen mit `-` statt unformatierten Zeilen
- Nummerierte Liste für Migration Guide
- Inline-Code mit Backticks: `` `HUAWEI_FILTER_TOLERANCE` ``
- Konsistente Einrückungen (2 Spaces)
- Leerzeilen zwischen Sections für bessere Lesbarkeit

## [1.6.2] - 2026-01-29

### Added

- **TRACE Log Level**: Ultra-detailed logging for deep debugging
  - New log level below DEBUG for maximum verbosity
  - Shows all Modbus byte arrays, register mappings, and library internals
  - Useful for protocol-level debugging and connection analysis
  - Added to config schema: `log_level: list(TRACE|DEBUG|INFO|WARNING|ERROR)`
  - External library log levels automatically adjusted:
    - TRACE: pymodbus=DEBUG, huawei_solar=DEBUG
    - DEBUG: pymodbus=INFO, huawei_solar=INFO
    - INFO+: pymodbus=WARNING, huawei_solar=WARNING

- **Comprehensive Test Suite**: 43 tests covering all critical functionality
  - **Unit Tests**: `test_filter.py` - 17 tests for filter logic
    - Basic filtering (negative values, drops, valid increases)
    - Edge cases (zero handling, exact tolerance, multiple drops)
    - Statistics tracking and reset functionality
  - **Integration Tests**: `test_integration.py` - 10 tests for component interaction
    - Transform pipeline with filter integration
    - MQTT client lifecycle (connect, publish, disconnect)
    - Error scenarios and recovery
  - **E2E Tests**: `test_e2e.py` - 7 tests for complete workflows
    - Full cycle with mock inverter and MQTT broker
    - Connection handling and status updates
    - Filter activity in real scenarios
  - **Warmup Tests**: `test_warmup.py` - 6 tests for warmup period
    - Initial value learning (60 second warmup)
    - Warmup completion behavior
    - Edge cases (immediate valid values, all filtered during warmup)
  - **Bug Regression Tests**: `test_hant_issue.py` - 3 tests for Issue #7
    - Verifies filter runs before MQTT publish
    - Ensures zero values never reach Home Assistant
    - Tests filter timing in complete pipeline
  - **Test Fixtures**: Mock inverter and MQTT broker with realistic scenarios
  - **CI/CD Integration**: GitHub Actions workflow for automated testing

- **Warmup Period**: Filter stability improvement for startup scenarios
  - First 60 seconds after startup treated as "warmup period"
  - Filter learns valid baseline values before applying strict filtering
  - Prevents false positives when starting with unknown state
  - Visual indicators in logs:
    - During warmup: `🔥 Warmup active (42/60s) - Learning valid values`
    - After warmup: `✅ Warmup complete (60/60s) - Filter now active`

### Changed

- **Enhanced Translations**: Improved German and English configuration descriptions
  - Added concrete examples (e.g., IP addresses, hostnames)
  - Included helpful hints (e.g., "Use core-mosquitto for Mosquitto add-on")
  - Explained all log levels with use cases and emoji indicators
  - Better guidance for beginners (slave_id ranges, timeout recommendations)
  - Multi-line descriptions with visual structure for better readability

- **Documentation Localization**: Fixed DOCS file naming convention
  - Renamed `DOCS_de.md` to `DOCS.de.md` (correct Home Assistant locale format)
  - Enables proper German documentation display for German-speaking users
  - English users see `DOCS.md`, German users see `DOCS.de.md`

- **Log Level Configuration**: Extended supported log levels in config.yaml
  - Schema updated from `DEBUG|INFO|WARNING|ERROR` to `TRACE|DEBUG|INFO|WARNING|ERROR`
  - Backwards compatible - existing configurations continue to work

- **Filter Logging**: Enhanced warmup status visibility
  - Clear indication when warmup is active vs. complete
  - Shows progress during warmup period (e.g., "42/60s")
  - Filter statistics only shown after warmup completion

### Fixed

- **Filter Warmup Edge Cases**: Improved stability during startup
  - Filter now correctly handles first valid values during warmup
  - Prevents false filtering of legitimate startup values
  - Better handling when all warmup values are filtered
  - Fixes potential issues with inverter restart scenarios

- **Filter Statistics**: Corrected counter behavior
  - Statistics now properly reset after reporting
  - No longer shows stale filter counts from previous periods
  - Accurate representation of filter activity over time

### Documentation

- **Translation Files**: Comprehensive German and English UI translations
  - `translations/de.yaml`: Complete German configuration UI
  - `translations/en.yaml`: Complete English configuration UI
  - All 11 configuration options fully documented
  - Includes examples, tips, and best practices for each field
  - Emoji indicators for better visual scanning (💡, 📍, ⏱️, 🔧, 🔍)

- **README Updates**:
  - Version bump references updated to 1.6.2
  - Added note about TRACE log level in feature list
  - Added note about comprehensive test suite
  - Improved troubleshooting section with log level recommendations
  - Updated "What's new" section with warmup period feature

- **Test Documentation**: Added comprehensive testing documentation
  - Test coverage overview in README
  - Instructions for running tests locally
  - Explanation of test fixtures and scenarios
  - CI/CD integration documentation

### Technical Details

- **Logging Enhancements**:
  - New `TRACE` constant (value: 5) in logging module
  - Custom `trace()` method added to Logger class
  - `_parse_log_level()` now handles TRACE string
  - `_configure_pymodbus()` and `_configure_huawei_solar()` support TRACE level
  - Log level mapping:
    ```
    TRACE (5)   → All libraries at DEBUG
    DEBUG (10)  → Libraries at INFO (filtered details)
    INFO (20)   → Libraries at WARNING (quiet)
    WARNING+    → Libraries at WARNING
    ```

- **Filter Improvements**:
  - `TotalIncreasingFilter` class now tracks warmup state
  - `_warmup_start` timestamp initialized on first use
  - `_is_warmup_complete()` method checks elapsed time
  - Warmup status included in filter logs
  - Statistics reset logic improved for accurate reporting

- **Test Infrastructure**:
  - `pytest` with coverage reporting (pytest-cov)
  - Mock fixtures for Modbus inverter and MQTT broker
  - Scenario-based testing with YAML configuration
  - Async test support with pytest-asyncio
  - Type checking with mypy in CI pipeline
  - Code quality checks with flake8

**Breaking Changes:** None - fully backwards compatible

**Upgrade Notes:**

- TRACE level available in config UI after update
- Existing DEBUG configurations remain unchanged
- Translation improvements visible immediately in UI
- German documentation automatically shown for German users
- Warmup period active by default (60s) - no configuration needed
- Filter behavior more stable during startup scenarios
- Tests can be run locally with `pytest tests/`

## [1.6.1] - 2026-01-29

### Fixed

- **Critical Bug Fix**: `total_increasing` filter now applies **before** MQTT publish instead of after
  - **Problem**: Previously the filter ran after MQTT publish, allowing zero values from Modbus read errors to reach Home Assistant for a brief moment
  - **Impact**: Utility Meter helpers would see the zero value and calculate incorrect daily totals (jumping by total accumulated energy)
  - **Solution**: Filter now runs in the data pipeline before publishing: `Modbus Read → Transform → Filter → MQTT Publish`
  - **Result**: Zero values are replaced with last valid value before they reach Home Assistant
- Fixes issue [#7](https://github.com/arboeh/huABus/issues/7) - Export energy counter drops to zero causing Utility Meter jumps

### Changed

- Filter now integrated into `main_once()` pipeline as explicit step
- Added filter timing measurement for performance monitoring
- Improved filter logging with cycle-by-cycle statistics

### Documentation

- **Quick Start Guide**: Added 5-minute onboarding for new users
  - Step-by-step installation with expected log outputs
  - Troubleshooting table for common first-time issues
  - Clear success indicators after first start

- **README Structure**: Improved hierarchy and navigation
  - Quick Start positioned before Features
  - Architecture badges added for platform visibility
  - Better visual separation between sections

## [1.6.0] - 2026-01-25

### Added

- **total_increasing Filter**: Prevents false counter resets in Home Assistant energy statistics
  - Filters negative values for energy counters (physically impossible)
  - Filters drops > 5% as likely Modbus read errors
  - Replaces invalid values with last valid value instead of 0
  - Configurable via `HUAWEI_FILTER_TOLERANCE` ENV variable (default: 0.05 = 5%)
  - Protects sensors: `energy_yield_accumulated`, `energy_grid_exported`, `energy_grid_accumulated`, `battery_charge_total`, `battery_discharge_total`

- **Automatic Filter Reset**: Filter state is reset on connection errors to prevent stale values
  - Reset triggers: Timeout, Modbus exception, Connection refused, Unexpected errors
  - Ensures fresh state after inverter restart or reconnect

- **Filter Status Indication**: Cycle summary now shows when values were filtered
  - INFO level: `📊 Published - PV: 788W | AC Out: 211W | Grid: 11W | Battery: 569W 🔍[2 filtered]`
  - DEBUG level: Detailed filter statistics showing which sensors were affected
  - Helps quickly identify Modbus read issues during operation

- **Filter Statistics Logging**: Comprehensive filter monitoring at different log levels
  - INFO level: Summary every 20 cycles when filters were active
  - DEBUG level: Detailed statistics after each filtered cycle
  - Format: `🔍 Filter details: {'energy_yield_accumulated': 2, 'battery_charge_total': 1}`

### Fixed

- **datetime Serialization**: `startup_time` register now correctly converted to ISO string for JSON compatibility
  - Fixes "Object of type datetime is not JSON serializable" error
  - Converts to ISO format: `2026-01-25T06:30:00`

- **Exception Handling**: Improved Modbus exception catching to avoid BaseException errors
  - Simplified to single `except Exception` with internal type checking
  - More robust handling when pymodbus exceptions are not available

### Changed

- **Enhanced Code Documentation**: Extensive German inline comments added across all modules
  - Every function documented with purpose, logic, examples
  - Technical decisions explained (why 5% tolerance, why filter reset, etc.)
  - Hardware dependencies and optional features clearly marked
  - Improved maintainability for future development

- **Cycle Summary Logging**: `log_cycle_summary()` now includes real-time filter status
  - Shows count of filtered values in main INFO log line
  - No additional log lines needed for basic filter awareness
  - Detailed breakdown available at DEBUG level

### Technical Details

- New module: `modbus_energy_meter/total_increasing_filter.py`
  - Singleton pattern with `get_filter()` and `reset_filter()` functions
  - Stores last valid values per sensor key
  - 5% tolerance prevents false positives during concurrent register updates
  - Filter statistics tracking for debugging and monitoring

- `transform.py` enhancements:
  - `_apply_total_increasing_filter()` function integrated into transform pipeline
  - `get_value()` now handles datetime objects via `.isoformat()`
  - Filter applied after mapping but before cleanup

- `main.py` improvements:
  - Filter reset added to all error handlers (timeout, modbus_exception, connection_refused, unexpected)
  - `log_cycle_summary()` enhanced with inline filter status indicator
  - Filter statistics logged at INFO level (periodic) and DEBUG level (detailed)
  - Simplified exception handling structure

**Breaking Changes:** None - fully backwards compatible

**Upgrade Notes:**

- Filter is enabled by default with 5% tolerance
- Filter activity visible at INFO level in cycle summary
- Detailed filter statistics available with `HUAWEI_LOG_LEVEL=DEBUG`

## [1.5.1] - 2026-01-18

### Fixed

- **Library Version Detection**: Startup logs now correctly display installed versions of `huawei-solar`, `pymodbus`, and `paho-mqtt`
  - Previously showed "unknown" due to hardcoded placeholder in `run.sh`
  - Now dynamically detects versions via Python's `__version__` attribute

### Changed

- **Startup Information**: Enhanced system info display with actual library versions

  [18:01:44] INFO: >> System Info:
  [18:01:44] INFO: - Python: 3.12.12
  [18:01:44] INFO: - huawei-solar: 2.5.0
  [18:01:44] INFO: - pymodbus: 3.11.4
  [18:01:44] INFO: - paho-mqtt: 2.1.0

### Technical Details

- `run.sh`: Added dynamic version detection using Python imports
- `main.py`: Enhanced `log_cycle_summary()` to include `battery_soc` in human-readable output
- No breaking changes - fully backwards compatible

## [1.5.0] - 2026-01-16

### Added

- **MQTT Connection Stability**: Wait loop and retry logic for reliable MQTT publishing
- **Connection State Tracking**: Global `_is_connected` flag prevents "not connected" errors
- **Development Environment**: PowerShell runner (`run_local.ps1`) and `.env` support for local testing
- **Exception Handling**: Improved Modbus exception handling with `is_modbus_exception()` helper

### Fixed

- **MQTT Publish Failures**: Added `wait_for_publish()` to all MQTT operations
- **Race Condition**: 1-second delay after MQTT connect ensures stable connection before publishing
- **paho-mqtt 2.x Support**: Version-compatible client creation with `CallbackAPIVersion.VERSION2`

### Changed

- **MQTT Client**: Callbacks now properly update connection state for reliable publish operations
- **Connection Timeout**: Increased from implicit to explicit 10-second wait with proper error handling

### Technical Details

- Connection wait loop polls `_is_connected` flag every 100ms up to 10 seconds
- All `publish()` calls now wait for confirmation with 1-2 second timeout
- Exception handling no longer uses `isinstance()` directly in except clauses to avoid BaseException errors

## [1.4.2] - 2026-01-09

### Added

- `.gitattributes` for enforced LF line endings across all text files (Linux/Docker compatibility)
- `.editorconfig` for standardized editor configuration (indent, charset, line endings)
- `.gitignore` with comprehensive Python/Docker/IDE exclusions
- GitHub Issue Templates for structured bug reports and feature requests
- GitHub Release Workflow for automated releases

### Changed

- Normalized all repository files to LF line endings (prevents `/bin/sh: bad interpreter` errors)
- Enhanced `.dockerignore` to properly include required Home Assistant files (CHANGELOG.md, DOCS.md)
- Improved `__init__.py` files with package docstrings for better code organization
- Updated `requirements.txt` with version constraints to prevent breaking changes

### Fixed

- Corrected `pymodbus` version requirement from non-existent `3.11.4` to `>=3.7.4,<4.0.0`
- Fixed potential line ending issues on Windows development environments
- Resolved `.dockerignore` accidentally excluding required add-on documentation

### Documentation

- Added troubleshooting guide for connection timeout issues (Slave ID configuration)
- Updated community support information with GitHub Issues link

## [1.4.1] - 2026-01-08

### Changed

- Enhanced startup logging with emoji icons (🚀🔌📡📍⏱️)
- Added visual separator lines in connection summary
- Set bashio log level dynamically based on HUAWEI_LOG_LEVEL
- Improved readability of startup configuration display

## [1.4.0] - 2026-01-08

### Features

- Error Tracker with intelligent error aggregation and downtime tracking
- Enhanced logging architecture with `log_cycle_summary()` function (supports JSON format for machine parsing)
- Bashio log level synchronization for consistent add-on logs across all components
- Performance optimization: `poll_interval` default lowered to 30s (previously 60s) for faster data updates

### Improvements

- ENV variables consistently named: `HUAWEI_SLAVE_ID` instead of `HUAWEI_MODBUS_DEVICE_ID` for better clarity
- Redundant logging removed: eliminated duplicate DEBUG statements in `main_once()` and `read_registers()`
- `publish_status()` optimized to DEBUG-level only (was INFO + DEBUG before)
- Dockerfile simplified: huawei_solar library patch removed (apply manually if needed for unknown enum values)
- run.sh refactored: removed legacy debug mode code, added case-based log level mapping
- DOCS.md fully synchronized with config.yaml defaults and updated examples

### Bugfixes

- Docstrings corrected: `publish_data()` now correctly documents exception behavior
- Connection recovery messages now include downtime duration in seconds
- Fixed inconsistent default values between config.yaml and main.py

### Technical Details

- Error recovery logging format: `Connection restored after {downtime}s ({attempts} failed attempts, {types} error types)`
- All configuration examples updated to reflect `poll_interval: 30` default
- Recommended settings table adjusted: Standard scenario now 30s instead of 60s

**Breaking Changes:** None - fully backwards-compatible with existing configurations
