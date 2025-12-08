# Changelog

## [Unreleased]

### Added
- [ ] Neue Features hier dokumentieren

### Fixed
- [ ] Bugfixes hier dokumentieren

### Changed
- [ ] Änderungen hier dokumentieren

## [1.0.7] - 2025-12-08

### Fixed
- **Kritischer Fix:** `UnboundLocalError` in `mqtt.py::get_mqtt_client()` behoben
  - Variable `base_topic` wurde vor Definition verwendet
  - Korrekte Reihenfolge: ENV-Variable abrufen → dann LWT-Setup
- **bashio-Kompatibilität:** Rückkehr zu bewährtem `#!/usr/bin/with-contenv bashio` Shebang
  - Behebt `bashio::log.info: not found` und `bashio::config: not found` Errors
  - Stellt volle Supervisor API-Funktionalität wieder her
- **Python Logging:** Vollständige Logging-Handler-Initialisierung für alle Module
  - `huawei.main`, `huawei.mqtt`, `huawei.transform` erhalten korrekte StreamHandler
  - DEBUG-Logs jetzt vollständig sichtbar (vorher nur bashio-Logs)
- **Umgebungsvariablen:** Robuste Validierung und Fallbacks für alle ENV-Vars
  - Verhindert `HUAWEI_MODBUS_MQTT_TOPIC not set – exiting` Crashes

### Changed
- **`run.sh` stabilisiert:** 
  - Bewährtes Original-Skript mit `python3 -u` (statt `exec`) für maximale Kompatibilität
  - Legacy `debug: true` Flag überschreibt `log_level` korrekt (v1.0.6 Feature)
  - Vollständige bashio::services mqtt Integration wiederhergestellt
- **Logging-Format:** Standardisiert auf `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Performance-Warnungen:** Verbesserte Cycle-Time-Monitoring mit präziseren Timings

### Added
- **Handler-Initialisierung:** Automatische StreamHandler-Erstellung für modulare Logger
- **Debug-Validierung:** ENV-Variablen-Debug-Output in `init()` für Fehlersuche
- **Fallback-Logging:** Kritische Logs auch bei fehlenden Handlern sichtbar

## [1.0.6] - 2025-12-08

### Added
- Detailiertes Debug-Logging der ENV-Variablen-Konfiguration im Startskript
- Erweiterte Performance-Metriken (Modbus/Transform/MQTT Timings pro Zyklus)

### Changed
- `run.sh` optimiert für maximale bashio-Kompatibilität
- Verbesserte Legacy `debug` Flag Integration mit `log_level`

### Fixed
- Fehlende Python-Logs bei bashio-only Ausgaben
- `HUAWEI_LOG_LEVEL` Umgebungsvariable korrekt gesetzt
- `AsyncHuaweiSolar` API vollständig implementiert

## [1.0.5] - 2025-12-08

### Added
- Separate Log-Level-Kontrolle für pymodbus Library (reduziert Logging-Overhead)
- MQTT Retain-Flag für `publish_data()` zur besseren Integration
- Null-Werte-Behandlung in `transform.py` für kritische Datenpunkte
- Fallback auf 0 für fehlende/null-Werte bei `power_active`, `power_input`, `meter_power_active`, `battery_power`, `battery_soc`
- Pymodbus-Logger bei INFO/WARNING/ERROR automatisch auf WARNING-Level
- Huawei-Solar Library Logger entsprechend globalem Log-Level konfiguriert

### Changed
- MQTT-Daten mit `retain=True` publiziert
- Pymodbus-Logs nur bei DEBUG oder WARNING/ERROR
- Kritische Sensor-Werte nie null, sondern standardmäßig 0
- Verbesserte Fehlerbehandlung für fehlende Register-Werte

### Fixed
- EVCC "outdated" Fehler durch fehlendes retain-Flag behoben
- EVCC `strconv.ParseFloat: parsing "<nil>"` durch Null-Werte-Fix behoben
- Übermäßige pymodbus ERROR-Logs bei normalem Betrieb reduziert

## [1.0.4] - 2025-12-08

### Added
- Konfigurierbarer Log-Level über `log_level` Option (DEBUG, INFO, WARNING, ERROR)
- Strukturiertes Logging mit separaten Loggern (`huawei.main`, `huawei.mqtt`, `huawei.transform`)
- Performance-Messung für Modbus-Reads, Transformation und MQTT-Publishing
- Detaillierte Debug-Logs mit Zeitmessungen pro Zyklus
- Zyklus-Zähler und Register-Read-Statistiken (erfolgreich/fehlgeschlagen)

### Changed
- Logging-Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- `get_value()` Funktion in `transform.py` optimiert
- Enum-/Datetime-Werte automatisch konvertiert

### Removed
- Unnötige Hilfsfunktionen in `transform.py`

## [1.0.3] - 2025-12-07

### Fixed
- Wechsel von `HuaweiSolarBridge` auf `AsyncHuaweiSolar` (neue huawei-solar API)
- Bridge-Instantiierungsfehler behoben
- Nicht unterstützte Register (Illegal Data Address) ohne Zyklusabbruch

### Changed
- Registerbasiertes Auslesen mit `AsyncHuaweiSolar.get()`
- Erweiterte Debug-Logs für fehlgeschlagene Register

## [1.0.2] - 2025-12-06

### Fixed
- `HuaweiSolarBridge.create()` Parameter-Fehler
- DecodeError-Handling für unbekannte Register (Unit-Code 780)
- Robustere Modbus-Fehlerbehandlung
- `heartbeat` Funktionsplatzierung

### Changed
- `huawei-solar` >=2.3.0, `pymodbus` >=3.8.6
- Separate Exception-Behandlung (`DecodeError`, `ReadException`)

## [1.0.1] - 2025-12-05

### Fixed
- DecodeError-Handling für unbekannte Register
- Verbesserte Modbus-Kommunikation

### Changed
- huawei-solar Library Update
- Erweiterte Logging-Ausgaben

## [1.0.0] - 2025-12-04

### Added
- Erste stabile Version
- GitHub Actions Release-Workflow
- Version-Badge in README

### Changed
- Von 0.9.0-beta → 1.0.0 (keine Breaking Changes)

## [0.9.0-beta] - 2025-12-03

### Added
- Initial beta release
- Modbus TCP zu Huawei Solar Inverter
- Automatische MQTT Discovery für Home Assistant
- Batterie-, PV-String-, Netz-Monitoring
- Konfigurierbar über HA UI

### Known Issues
- Erweiterte Tests laufen noch
