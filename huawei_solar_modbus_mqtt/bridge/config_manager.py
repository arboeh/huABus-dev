# bridge/config_manager.py

"""Configuration Manager for Huawei Solar Modbus MQTT Bridge.

Handles configuration loading from:
- Environment variables (Docker/Add-on runtime)
- /data/options.json (Home Assistant Add-on)
- Default values (development)

Supports both flat (old) and nested (new) configuration structures
with automatic migration.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional, cast

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manage add-on configuration with validation and migration."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize ConfigManager.

        Args:
            config_path: Path to options.json (default: /data/options.json)
        """
        self.config_path = config_path or Path("/data/options.json")
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file or environment variables."""
        if self.config_path.exists():
            logger.info(f"Loading configuration from {self.config_path}")
            with open(self.config_path, "r") as f:
                raw_config = json.load(f)
            self._config = self._migrate_config(raw_config)
        else:
            logger.info("No config file found, loading from environment variables")
            self._config = self._load_from_env()

    def _migrate_config(self, config: dict) -> dict:
        """Migrate old flat config to new nested structure.

        Args:
            config: Configuration dictionary (might be old or new format)

        Returns:
            Configuration in new nested format
        """
        # Check if already new format
        if "modbus" in config and isinstance(config["modbus"], dict):
            logger.debug("Configuration already in new nested format")
            return config

        logger.warning("Detected old configuration format. Migrating to new structure...")

        # Migrate from old flat structure
        migrated = {
            "modbus": {
                "host": config.get("modbus_host", "192.168.1.100"),
                "port": config.get("modbus_port", 502),
                "auto_detect_slave_id": config.get("auto_detect_slave_id", True),
                "slave_id": config.get("slave_id", 1),
            },
            "mqtt": {
                "broker": config.get("mqtt_host", "localhost"),
                "port": config.get("mqtt_port", 1883),
                "username": config.get("mqtt_user"),
                "password": config.get("mqtt_password"),
                "topic_prefix": config.get("mqtt_topic", "huawei-solar"),
            },
            "advanced": {
                "log_level": config.get("log_level", "INFO"),
                "status_timeout": config.get("status_timeout", 180),
                "poll_interval": config.get("poll_interval", 30),
            },
        }

        logger.info("Migration completed successfully")
        return migrated

    def _load_from_env(self) -> dict:
        """Load configuration from environment variables.

        Returns:
            Configuration dictionary in new nested format
        """
        return {
            "modbus": {
                "host": os.getenv("HUAWEI_MODBUS_HOST", "192.168.1.100"),
                "port": int(os.getenv("HUAWEI_MODBUS_PORT", "502")),
                "auto_detect_slave_id": self._parse_bool_env("HUAWEI_SLAVEID_AUTO", default=True),
                "slave_id": self._parse_int_env("HUAWEI_SLAVE_ID", default=1),
            },
            "mqtt": {
                "broker": os.getenv("HUAWEI_MODBUS_MQTT_BROKER", "localhost"),
                "port": int(os.getenv("HUAWEI_MODBUS_MQTT_PORT", "1883")),
                "username": os.getenv("HUAWEI_MODBUS_MQTT_USER"),
                "password": os.getenv("HUAWEI_MODBUS_MQTT_PASSWORD"),
                "topic_prefix": os.getenv("HUAWEI_MODBUS_MQTT_TOPIC", "huawei-solar"),
                "discovery": True,  # Always enabled
            },
            "advanced": {
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "status_timeout": int(os.getenv("MQTT_STATUS_TIMEOUT", "180")),
                "poll_interval": int(os.getenv("MQTT_POLL_INTERVAL", "30")),
            },
        }

    @staticmethod
    def _parse_bool_env(key: str, default: bool = False) -> bool:
        """Parse boolean from environment variable."""
        value = os.getenv(key)

        # Wenn nicht gesetzt oder leer → default verwenden
        if not value or not value.strip():
            return default

        value_lower = value.strip().lower()

        if value_lower in ("true", "yes", "1", "on"):
            return True
        if value_lower in ("false", "no", "0", "off"):
            return False

        # Unbekannter Wert → default
        return default

    @staticmethod
    def _parse_int_env(key: str, default: int) -> int:
        """Parse integer from environment variable."""
        value = os.getenv(key)
        if not value or value.lower() in ("null", "none", ""):
            return default
        try:
            return int(value.strip())
        except ValueError:
            logger.warning(f"Invalid integer for {key}={value}, using default: {default}")
            return default

    # === Modbus Configuration ===

    @property
    def modbus_host(self) -> str:
        """Get Modbus host."""
        return cast(str, self._config["modbus"].get("host", "192.168.1.100"))

    @property
    def modbus_port(self) -> int:
        """Get Modbus port."""
        return cast(int, self._config["modbus"].get("port", 502))

    @property
    def auto_detect_slave_id(self) -> bool:
        """Get auto-detect flag."""
        return cast(bool, self._config["modbus"].get("auto_detect_slave_id", True))

    @property
    def slave_id(self) -> int | None:
        """Get Slave ID."""
        value = self._config["modbus"].get("slave_id")
        return cast(int, value) if value is not None else None

    @property
    def mqtt_broker(self) -> str:
        """Get MQTT broker."""
        return cast(str, self._config["mqtt"].get("broker", "localhost"))

    @property
    def mqtt_port(self) -> int:
        """Get MQTT port."""
        return cast(int, self._config["mqtt"].get("port", 1883))

    @property
    def mqtt_username(self) -> str | None:
        """Get MQTT username."""
        username = self._config["mqtt"].get("username")
        if not username or username == "":
            return None
        return cast(str, username)

    @property
    def mqtt_password(self) -> str | None:
        """Get MQTT password."""
        password = self._config["mqtt"].get("password")
        if not password or password == "":
            return None
        return cast(str, password)

    @property
    def mqtt_topic_prefix(self) -> str:
        """Get MQTT topic prefix."""
        return cast(str, self._config["mqtt"].get("topic_prefix", "huawei-solar"))

    @property
    def log_level(self) -> str:
        """Get log level."""
        return cast(str, self._config["advanced"].get("log_level", "INFO"))

    @property
    def status_timeout(self) -> int:
        """Get status timeout."""
        return cast(int, self._config["advanced"].get("status_timeout", 180))

    @property
    def poll_interval(self) -> int:
        """Get poll interval."""
        return cast(int, self._config["advanced"].get("poll_interval", 30))

    def log_config(self, hide_passwords: bool = True) -> None:
        """
        Log current configuration (called by main at startup).

        Args:
            hide_passwords: Mask passwords in logs (default: True)
        """
        # Keine Separator-Linien mehr!
        logger.info("Configuration:")
        logger.info("  Modbus:")
        logger.info(f"    Host: {self.modbus_host}")
        logger.info(f"    Port: {self.modbus_port}")

        if self.auto_detect_slave_id:
            logger.info("    Slave ID: auto-detect enabled")
        else:
            logger.info(f"    Slave ID: {self.slave_id} (manual)")

        logger.info("  MQTT:")
        logger.info(f"    Broker: {self.mqtt_broker}:{self.mqtt_port}")

        # Username/Password nur wenn gesetzt
        if self.mqtt_username:
            password_display = "***" if hide_passwords and self.mqtt_password else self.mqtt_password
            logger.info(f"    Auth: {self.mqtt_username} / {password_display or '(no password)'}")
        else:
            logger.info("    Auth: none")

        logger.info(f"    Topic: {self.mqtt_topic_prefix}")

        logger.info("  Advanced:")
        logger.info(f"    Log Level: {self.log_level}")
        logger.info(f"    Status Timeout: {self.status_timeout}s")
        logger.info(f"    Poll Interval: {self.poll_interval}s")
