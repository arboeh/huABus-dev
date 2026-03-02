ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# System-Dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    git

WORKDIR /app

# Projekt-Metadaten kopieren
COPY pyproject.toml ./

# Hatch installieren
RUN pip3 install --break-system-packages --no-cache-dir hatch

# Projekt-Abhängigkeiten installieren
RUN hatch env create default \
    && hatch run pip install -e .

# Rest des Projekts kopieren
COPY bridge ./bridge/
COPY run.sh /
RUN chmod a+x /run.sh

# Labels für Home Assistant Addon
LABEL \
    io.hass.name="huABus - Huawei Solar Modbus to MQTT" \
    io.hass.description="Huawei Solar Modbus via MQTT + Auto-Discovery" \
    io.hass.type="addon" \
    io.hass.arch="aarch64|amd64|armhf|armv7|i386"

# Healthcheck für Docker
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "python3.*bridge.main" > /dev/null || exit 1

# Start-Skript
CMD ["/run.sh"]
