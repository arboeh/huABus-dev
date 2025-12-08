ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash

# Set working directory
WORKDIR /app

# Copy and install Python requirements (cached layer)
COPY requirements.txt ./
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

# Patch huawei_solar library (tolerate unknown enum values)
# Dynamically find Python version instead of hardcoded 3.12
RUN PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')") && \
    REGISTERS_PATH="/usr/lib/python${PYTHON_VERSION}/site-packages/huawei_solar/registers.py" && \
    if [ -f "$REGISTERS_PATH" ]; then \
        sed -i "s/result = self.unit\[result\]/result = self.unit.get(result, result)/" "$REGISTERS_PATH" && \
        echo "✓ Patched huawei_solar registers.py (Python ${PYTHON_VERSION})"; \
    else \
        echo "⚠ Warning: registers.py not found at $REGISTERS_PATH"; \
    fi

# Copy application files
COPY modbus_energy_meter ./modbus_energy_meter/
COPY huawei2mqtt.py ./
COPY run.sh /

# Make run script executable
RUN chmod a+x /run.sh

# Labels for metadata
LABEL \
    io.hass.name="Huawei Solar Modbus to MQTT" \
    io.hass.description="Huawei Solar Inverter via Modbus to MQTT with auto-discovery" \
    io.hass.version="1.1.1" \
    io.hass.type="addon" \
    io.hass.arch="aarch64|amd64|armhf|armv7|i386"

# Health check (optional - prüft ob Python-Prozess läuft)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "python3.*huawei2mqtt.py" > /dev/null || exit 1

CMD ["/run.sh"]
