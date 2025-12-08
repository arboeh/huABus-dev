#!/usr/bin/env bashio
set -e

bashio::log.info "Starting Huawei Solar Modbus to MQTT Add On v1.0.6"

# === ULTRA-ROBUSTE KONFIG-EXTRAKTION ===
get_config_safe() {
    local key="$1"
    local default="$2"
    # bashio::config ohne Fehler, mit Fallback
    bashio::config "${key}" 2>/dev/null || echo "${default}"
}

# Basis-Konfiguration
export HUAWEI_MODBUS_HOST=$(get_config_safe "modbus_host" "192.168.1.100")
export HUAWEI_MODBUS_PORT=$(get_config_safe "modbus_port" "502")
export HUAWEI_MODBUS_DEVICE_ID=$(get_config_safe "modbus_device_id" "1")
export HUAWEI_MODBUS_MQTT_TOPIC=$(get_config_safe "mqtt_topic" "huawei-solar")
export HUAWEI_STATUS_TIMEOUT=$(get_config_safe "status_timeout" "180")
export HUAWEI_POLL_INTERVAL=$(get_config_safe "poll_interval" "60")
export HUAWEI_LOG_LEVEL=$(get_config_safe "log_level" "INFO" | tr '[:lower:]' '[:upper:]')

# Legacy debug
if bashio::config.true "debug" 2>/dev/null; then
    export HUAWEI_MODBUS_DEBUG="yes"
    export HUAWEI_LOG_LEVEL="DEBUG"
fi

# MQTT - immer core-mosquitto (da bashio::services fehlschlägt)
export HUAWEI_MODBUS_MQTT_BROKER="core-mosquitto"
export HUAWEI_MODBUS_MQTT_PORT="1883"
export HUAWEI_MODBUS_MQTT_USER=""
export HUAWEI_MODBUS_MQTT_PASSWORD=""

bashio::log.info "=== FINAL CONFIGURATION ==="
bashio::log.info "Log: ${HUAWEI_LOG_LEVEL} | Inverter: ${HUAWEI_MODBUS_HOST}:${HUAWEI_MODBUS_PORT}"
bashio::log.info "MQTT: ${HUAWEI_MODBUS_MQTT_TOPIC} @ ${HUAWEI_MODBUS_MQTT_BROKER}:${HUAWEI_MODBUS_MQTT_PORT}"
bashio::log.info "=========================="

# KRITISCHE PRÜFUNG
if [ -z "$HUAWEI_MODBUS_HOST" ] || [ -z "$HUAWEI_MODBUS_MQTT_TOPIC" ]; then
    bashio::log.fatal "❌ CRITICAL: Missing config! HOST='${HUAWEI_MODBUS_HOST}' TOPIC='${HUAWEI_MODBUS_MQTT_TOPIC}'"
    exit 1
fi

bashio::log.info "✅ CONFIG OK - Starting Python..."

# 🚀 PYTHON MIT 100% LOG-ÜBERTRAGUNG
exec python3 -u /app/huawei2mqtt.py 2>&1
