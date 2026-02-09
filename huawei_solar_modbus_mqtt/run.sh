#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
# shellcheck disable=SC1008

VERSION=$(bashio::addon.version)

# Banner IMMER anzeigen
echo "[$(date +'%T')] INFO: =========================================================="
echo "[$(date +'%T')] INFO:  🌞 huABus v${VERSION}"
echo "[$(date +'%T')] INFO:  📦 https://github.com/arboeh/huABus"
echo "[$(date +'%T')] INFO: =========================================================="
echo "[$(date +'%T')] INFO: >> Starting huABus - Huawei Solar Modbus MQTT Add-on..."

# === Helper function for required config ===
get_required_config() {
	local key=$1
	local default=$2
	local value

	if bashio::config.has_value "$key"; then
		value=$(bashio::config "$key")
	elif [ -n "$default" ]; then
		value="$default"
		bashio::log.warning "Config key '$key' not found, using default: $default"
	else
		bashio::log.fatal "Required configuration key missing: $key"
		exit 1
	fi

	echo "$value"
}

# === Modbus Configuration ===
# shellcheck disable=SC2155
export HUAWEI_MODBUS_HOST=$(get_required_config 'modbus_host')
export HUAWEI_MODBUS_PORT=$(get_required_config 'modbus_port' '502')
export HUAWEI_SLAVEID_AUTO=$(get_required_config 'modbus_auto_detect_slave_id' 'true')
export HUAWEI_SLAVE_ID=$(get_required_config 'modbus_slave_id' '1')

# === MQTT Topic & Discovery ===
export HUAWEI_MODBUS_MQTT_TOPIC=$(get_required_config 'mqtt_topic_prefix' 'huawei-solar')

# === Advanced Configuration ===
export HUAWEI_STATUS_TIMEOUT=$(get_required_config 'status_timeout' '180')
export HUAWEI_POLL_INTERVAL=$(get_required_config 'poll_interval' '30')
export HUAWEI_LOG_LEVEL=$(get_required_config 'log_level' 'INFO')

echo "[$(date +'%T')] INFO: >> Log level: ${HUAWEI_LOG_LEVEL}"

# Set bashio log level to match
case "${HUAWEI_LOG_LEVEL}" in
TRACE)
	bashio::log.level debug # bashio doesn't have TRACE, use DEBUG
	;;
DEBUG)
	bashio::log.level debug
	;;
WARNING)
	bashio::log.level warning
	;;
ERROR)
	bashio::log.level error
	;;
*)
	bashio::log.level info
	;;
esac

# === MQTT Broker (Custom or HA Service) ===
if bashio::config.has_value 'mqtt_broker' && [ -n "$(bashio::config 'mqtt_broker')" ]; then
	# shellcheck disable=SC2155
	export HUAWEI_MODBUS_MQTT_BROKER=$(bashio::config 'mqtt_broker')
	MQTT_SOURCE="custom"
else
	if bashio::services.available mqtt; then
		# shellcheck disable=SC2155
		export HUAWEI_MODBUS_MQTT_BROKER=$(bashio::services mqtt "host")
		MQTT_SOURCE="HA service"
	else
		bashio::log.fatal "No MQTT broker configured and HA MQTT service not available!"
		exit 1
	fi
fi

# === MQTT Port ===
if bashio::config.has_value 'mqtt_port' && [ -n "$(bashio::config 'mqtt_port')" ]; then
	# shellcheck disable=SC2155
	export HUAWEI_MODBUS_MQTT_PORT=$(bashio::config 'mqtt_port')
else
	if bashio::services.available mqtt; then
		# shellcheck disable=SC2155
		export HUAWEI_MODBUS_MQTT_PORT=$(bashio::services mqtt "port")
	else
		export HUAWEI_MODBUS_MQTT_PORT=1883
		bashio::log.warning "MQTT port not configured, using default: 1883"
	fi
fi

# === MQTT User ===
if bashio::config.has_value 'mqtt_username' && [ -n "$(bashio::config 'mqtt_username')" ]; then
	# shellcheck disable=SC2155
	export HUAWEI_MODBUS_MQTT_USER=$(bashio::config 'mqtt_username')
	MQTT_AUTH="custom"
else
	if bashio::services.available mqtt; then
		# shellcheck disable=SC2155
		export HUAWEI_MODBUS_MQTT_USER=$(bashio::services mqtt "username")
		MQTT_AUTH="HA service"
	else
		export HUAWEI_MODBUS_MQTT_USER=""
		MQTT_AUTH="none"
	fi
fi

# === MQTT Password ===
if bashio::config.has_value 'mqtt_password' && [ -n "$(bashio::config 'mqtt_password')" ]; then
	# shellcheck disable=SC2155
	export HUAWEI_MODBUS_MQTT_PASSWORD=$(bashio::config 'mqtt_password')
else
	if bashio::services.available mqtt; then
		# shellcheck disable=SC2155
		export HUAWEI_MODBUS_MQTT_PASSWORD=$(bashio::services mqtt "password")
	else
		export HUAWEI_MODBUS_MQTT_PASSWORD=""
	fi
fi

# === Validation ===
if [ -z "$HUAWEI_MODBUS_HOST" ]; then
	bashio::log.fatal "Modbus host is required but not configured!"
	exit 1
fi

if [ -z "$HUAWEI_MODBUS_MQTT_BROKER" ]; then
	bashio::log.fatal "MQTT broker is required but not configured!"
	exit 1
fi

# === Connection Summary ===
echo "[$(date +'%T')] INFO: ----------------------------------------------------------"

# Slave ID Display Logic
if [ "${HUAWEI_SLAVEID_AUTO}" = "true" ]; then
	echo "[$(date +'%T')] INFO:  🔌 Inverter: ${HUAWEI_MODBUS_HOST}:${HUAWEI_MODBUS_PORT} (Slave ID: auto-detect)"
else
	echo "[$(date +'%T')] INFO:  🔌 Inverter: ${HUAWEI_MODBUS_HOST}:${HUAWEI_MODBUS_PORT} (Slave ID: ${HUAWEI_SLAVE_ID})"
fi

echo "[$(date +'%T')] INFO:  📡 MQTT: ${HUAWEI_MODBUS_MQTT_BROKER}:${HUAWEI_MODBUS_MQTT_PORT} (${MQTT_SOURCE})"

# Zeige MQTT Auth Status (ohne Credentials zu leaken)
if [ -n "${HUAWEI_MODBUS_MQTT_USER}" ]; then
	echo "[$(date +'%T')] INFO:  🔐 Auth: enabled (${MQTT_AUTH})"
else
	echo "[$(date +'%T')] INFO:  🔐 Auth: disabled"
fi

echo "[$(date +'%T')] INFO:  📍 Topic: ${HUAWEI_MODBUS_MQTT_TOPIC}"
echo "[$(date +'%T')] INFO:  ⏱️  Poll: ${HUAWEI_POLL_INTERVAL}s | Timeout: ${HUAWEI_STATUS_TIMEOUT}s"

# Registerzähler
REGISTER_COUNT=58
echo "[$(date +'%T')] INFO:  📊 Registers: ${REGISTER_COUNT} essential"
echo "[$(date +'%T')] INFO: ----------------------------------------------------------"

# === System Info ===
bashio::log.info ">> System Info:"
bashio::log.info "   - Python: $(python3 --version | cut -d' ' -f2)"

# Get package versions - using pip show with fallback
HUAWEI_SOLAR_VERSION=$(pip3 show huawei-solar 2>/dev/null | grep '^Version:' | awk '{print $2}')
PYMODBUS_VERSION=$(pip3 show pymodbus 2>/dev/null | grep '^Version:' | awk '{print $2}')
PAHO_VERSION=$(pip3 show paho-mqtt 2>/dev/null | grep '^Version:' | awk '{print $2}')

# Fallback to "unknown" if empty
HUAWEI_SOLAR_VERSION=${HUAWEI_SOLAR_VERSION:-unknown}
PYMODBUS_VERSION=${PYMODBUS_VERSION:-unknown}
PAHO_VERSION=${PAHO_VERSION:-unknown}

bashio::log.info "   - huawei-solar: ${HUAWEI_SOLAR_VERSION}"
bashio::log.info "   - pymodbus: ${PYMODBUS_VERSION}"
bashio::log.info "   - paho-mqtt: ${PAHO_VERSION}"
bashio::log.info "   - Architecture: $(uname -m)"

# ============================================================
# === TEST MODE GUARD - Exit here when running BATS tests ===
# ============================================================
if [ "${BATS_TEST_MODE:-false}" = "true" ]; then
	bashio::log.info ">> Test mode enabled - skipping application start"
	return 0
fi
# ============================================================

echo "[$(date +'%T')] INFO: >> Starting Python application..."

# Start Python application
cd /app || exit 1
exec python3 -u -m bridge.main
