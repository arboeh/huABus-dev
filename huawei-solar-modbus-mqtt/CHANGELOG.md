# Changelog

## [1.3.0] - 2025-12-09
### 🏗️ **CODE-REFACTORING**
**Configs ausgelagert**

### Added
- **Config-Modul (`config/`):** Zentrale Verwaltung
  - `registers.py`: 47 Essential Registers
  - `mappings.py`: Register-Mapping + Defaults
  - `sensors_mqtt.py`: 58 Sensor-Definitionen
- **5 neue Register (42 → 47):**
  - `active_power_meter` (37113): Grid Power
  - `storage_charge/discharge_capacity_today`: Battery Today
  - `meter_status`: Meter Online-Status
  - `reactive_power_meter`: Grid Reactive Power
- **13 neue Entities (46 → 59):** Battery Bus, Line Voltages, Grid Details

### Changed
- **Package-Struktur:** `main.py` + `mqtt_client.py` jetzt in `modbus_energy_meter/`
- **Code-Reduktion:** `mqtt_client.py` 700 → 180 Zeilen (-74%)
- **Module-Import:** `python3 -m modbus_energy_meter.main` statt direkter Ausführung

### Performance
| Metric | v1.2.1 | v1.3.0 |
|--------|--------|--------|
| Registers | 42 | **47** (+12%) |
| Entities | 46 | **59** (+28%) |
| Cycle Time | 4,6s | **5,2s** (+0,6s) |

---

## [1.2.1] - 2025-12-09
**Bugfix:** Persistente MQTT-Verbindung, Status-Flackern behoben  
**Entities** bleiben dauerhaft "available", keine Connection-Timeouts mehr

---

## [1.2.0] - 2025-12-09
**Extended Registers:** +8 neue Register (34 → 42)  
**Device Info:** Model, Serial, Rated Power, Efficiency, Alarms  
**Entities:** 38 → 46

---

## [1.1.2] - 2025-12-08
**Code Quality:** Refactoring, Dependencies reduziert (7 → 5 Pakete)  
**Dockerfile:** Dynamische Python-Version, Health Check

---

## [1.1.1] - 2025-12-08
**Performance:** Nur Essential Registers (21), <3s Cycle-Time  
**Optimierung:** 94% weniger Register-Reads

---

## [1.1.0] - 2025-12-08
**Major Performance:** Parallele Modbus-Reads (240s → 30s, 8x schneller)  
**Batch-Processing:** 20 Register parallel pro Batch

---

## [1.0.7] - 2025-12-08
**Bugfixes:** `UnboundLocalError` in mqtt.py, bashio-Kompatibilität

---

## [1.0.6] - 2025-12-08
**Logging:** ENV-Variablen-Debug, Performance-Metriken

---

## [1.0.5] - 2025-12-08
**MQTT:** `retain=True` für Integrationen, Null-Werte-Fallback

---

## [1.0.4] - 2025-12-08
**Logging:** Konfigurierbarer `log_level`, Performance-Messung

---

## [1.0.3] - 2025-12-07
**Migration:** `HuaweiSolarBridge` → `AsyncHuaweiSolar`

---

## [1.0.2] - 2025-12-06
**Bugfixes:** Modbus DecodeError, robustere Exception-Behandlung

---

## [1.0.1] - 2025-12-05
**Bugfixes:** DecodeError für unbekannte Register

---

## [1.0.0] - 2025-12-04
**Erste stabile Version** - GitHub Actions, Version-Badge

---

## [0.9.0-beta] - 2025-12-03
**Initial Beta Release**  
Modbus TCP → MQTT Discovery, Batterie/PV/Netz-Monitoring
