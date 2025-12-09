# Huawei Solar Modbus → Home Assistant via MQTT

🌐 [English](README.md) | 🇩🇪 **Deutsch**

[![aarch64](https://img.shields.io/badge/aarch64-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![amd64](https://img.shields.io/badge/amd64-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![armhf](https://img.shields.io/badge/armhf-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![armv7](https://img.shields.io/badge/armv7-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![i386](https://img.shields.io/badge/i386-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![release](https://img.shields.io/github/v/release/arboeh/homeassistant-huawei-solar-addon?display_name=tag)](https://github.com/arboeh/homeassistant-huawei-solar-addon/releases/latest)

Home Assistant Add-on für Huawei SUN2000 Wechselrichter via Modbus TCP → MQTT mit automatischer Discovery.

**Version 1.2.1** - 42 Register, 46 Entitäten, 4,6s Cycle-Time

## Features

- **Modbus TCP** → MQTT Auto-Discovery (46 Entitäten)
- **Monitoring:** Batterie, PV-Strings (1-4), Netz (3-Phasen), Ertrag
- **Geräte-Info:** Modell, Seriennummer, Nennleistung, Effizienz, Alarme
- **Performance:** 4,6s Cycle, konfigurierbares Poll-Interval

## Installation

1. [![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Farboeh%2Fhomeassistant-huawei-solar-addon)
2. "Huawei Solar Modbus to MQTT" installieren
3. Konfigurieren → Starten
4. Entitäten erscheinen: **Einstellungen → Geräte & Dienste → MQTT → "Huawei Solar Inverter"**

## Konfiguration

**Minimal:**

    modbus_host: "192.168.1.100"
    modbus_device_id: 1
    poll_interval: 30

**Erweitert:**

    modbus_host: "192.168.1.100" # Inverter IP
    modbus_port: 502 # Standard: 502
    modbus_device_id: 1 # Slave ID (1 oder 16)
    mqtt_host: "core-mosquitto" # Leer = Auto
    mqtt_topic: "huawei-solar"
    poll_interval: 30 # Sekunden (30-60 empfohlen)
    log_level: "INFO" # DEBUG/INFO/WARNING/ERROR

## Wichtigste Entitäten

**Leistung/Energie:** `solar_power`, `grid_power`, `battery_power`, `pv1-4_power`, `daily_yield`, `total_yield`  
**Batterie:** `battery_soc`, `battery_charge/discharge_today`, `battery_total_charge/discharge`  
**Netz:** `grid_voltage_phase_a/b/c`, `line_voltage_a_b/b_c/c_a`, `grid_frequency`  
**Inverter:** `inverter_temperature`, `efficiency`, `reactive_power`, `insulation_resistance`  
**Gerät:** `model_name`, `serial_number`, `rated_power`, `startup_time`, `alarm_1`

## Fehlerbehebung

**Modbus:** TCP am Inverter aktivieren, IP prüfen, Slave IDs `1`/`16`/`0` testen, `log_level: DEBUG`  
**MQTT:** `mqtt_host: "core-mosquitto"` nutzen, Credentials leer lassen für Auto-Discovery  
**Performance:** Bei Cycle-Warnungen `poll_interval` erhöhen (30-60s empfohlen)

**Logs:** Einstellungen → Add-ons → Huawei Solar → Log

## Changelog

**1.2.1** (2025-12-09) - Bugfix: Online Status & Flackern der Sensoren behoben
**1.2.0** (2025-12-09) - Erweiterte Register: Geräte-Info, Effizienz, Alarme (+8 Register, 46 Entitäten)  
**1.1.2** (2025-12-08) - Code-Refactoring, Dependencies reduziert (7→5 Pakete)  
**1.1.1** (2025-12-08) - Nur Essential Registers (21), <3s Cycle-Time

[Vollständiger Changelog](CHANGELOG.md)

## Credits

**Basiert auf:** [mjaschen/huawei-solar-modbus-to-mqtt](https://github.com/mjaschen/huawei-solar-modbus-to-mqtt)  
**Entwickelt von:** [arboeh](https://github.com/arboeh) | **Lizenz:** MIT
