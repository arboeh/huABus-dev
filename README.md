# Huawei Solar Modbus → Home Assistant via MQTT

🌐 **English** | 🇩🇪 [Deutsch](README_de.md)

[![aarch64](https://img.shields.io/badge/aarch64-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![amd64](https://img.shields.io/badge/amd64-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![armhf](https://img.shields.io/badge/armhf-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![armv7](https://img.shields.io/badge/armv7-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![i386](https://img.shields.io/badge/i386-yes-green.svg)](https://github.com/arboeh/homeassistant-huawei-solar-addon)
[![release](https://img.shields.io/github/v/release/arboeh/homeassistant-huawei-solar-addon?display_name=tag)](https://github.com/arboeh/homeassistant-huawei-solar-addon/releases/latest)

Home Assistant Add-on for Huawei SUN2000 inverters via Modbus TCP → MQTT with automatic discovery.

**Version 1.2.1** - 42 registers, 46 entities, 4.6s cycle time

## Features

- **Modbus TCP** → MQTT Auto-Discovery (46 entities)
- **Monitoring:** Battery, PV strings (1-4), Grid (3-phase), Yield
- **Device Info:** Model, Serial, Rated Power, Efficiency, Alarms
- **Performance:** 4.6s cycle, configurable poll interval

## Installation

1. [![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Farboeh%2Fhomeassistant-huawei-solar-addon)
2. Install "Huawei Solar Modbus to MQTT"
3. Configure → Start
4. Entities appear: **Settings → Devices & Services → MQTT → "Huawei Solar Inverter"**

## Configuration

**Minimal:**

    modbus_host: "192.168.1.100"
    modbus_device_id: 1
    poll_interval: 30

**Advanced:**

    modbus_host: "192.168.1.100" # Inverter IP
    modbus_port: 502 # Default: 502
    modbus_device_id: 1 # Slave ID (1 or 16)
    mqtt_host: "core-mosquitto" # Empty = auto
    mqtt_topic: "huawei-solar"
    poll_interval: 30 # Seconds (30-60 recommended)
    log_level: "INFO" # DEBUG/INFO/WARNING/ERROR

## Main Entities

**Power/Energy:** `solar_power`, `grid_power`, `battery_power`, `pv1-4_power`, `daily_yield`, `total_yield`  
**Battery:** `battery_soc`, `battery_charge/discharge_today`, `battery_total_charge/discharge`  
**Grid:** `grid_voltage_phase_a/b/c`, `line_voltage_a_b/b_c/c_a`, `grid_frequency`  
**Inverter:** `inverter_temperature`, `efficiency`, `reactive_power`, `insulation_resistance`  
**Device:** `model_name`, `serial_number`, `rated_power`, `startup_time`, `alarm_1`

## Troubleshooting

**Modbus:** Enable TCP on inverter, check IP, try Slave IDs `1`/`16`/`0`, use `log_level: DEBUG`  
**MQTT:** Use `mqtt_host: "core-mosquitto"`, leave credentials empty for auto-discovery  
**Performance:** Increase `poll_interval` if cycle warnings appear (30-60s recommended)

**Logs:** Settings → Add-ons → Huawei Solar → Log

## Changelog

**1.2.1** (2025-12-09) - Bugfix: Online status & sensor flickering
**1.2.0** (2025-12-09) - Extended registers: Device info, efficiency, alarms (+8 registers, 46 entities)  
**1.1.2** (2025-12-08) - Code refactoring, dependencies reduced (7→5 packages)  
**1.1.1** (2025-12-08) - Essential registers only (21), <3s cycle time

[Full Changelog](CHANGELOG.md)

## Credits

**Based on:** [mjaschen/huawei-solar-modbus-to-mqtt](https://github.com/mjaschen/huawei-solar-modbus-to-mqtt)  
**Developed by:** [arboeh](https://github.com/arboeh) | **License:** MIT
