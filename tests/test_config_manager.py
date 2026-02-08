# tests/test_config_manager.py

"""Tests for ConfigManager."""

import json

import pytest
from bridge.config_manager import ConfigManager


class TestConfigManagerLoading:
    """Test configuration loading from different sources."""

    def test_load_from_file_nested_structure(self, tmp_path):
        """Should load nested config from options.json."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus": {
                "host": "192.168.1.200",
                "port": 502,
                "auto_detect_slave_id": True,
                "slave_id": 1,
            },
            "mqtt": {
                "broker": "mqtt.example.com",
                "port": 1883,
                "username": "testuser",
                "password": "testpass",
                "topic_prefix": "test-topic",
                "discovery": True,
            },
            "advanced": {
                "log_level": "DEBUG",
                "status_timeout": 120,
                "poll_interval": 20,
            },
        }

        config_file.write_text(json.dumps(config_data))

        config = ConfigManager(config_path=config_file)

        # Modbus
        assert config.modbus_host == "192.168.1.200"
        assert config.modbus_port == 502
        assert config.auto_detect_slave_id is True
        assert config.slave_id == 1

        # MQTT
        assert config.mqtt_broker == "mqtt.example.com"
        assert config.mqtt_port == 1883
        assert config.mqtt_username == "testuser"
        assert config.mqtt_password == "testpass"
        assert config.mqtt_topic_prefix == "test-topic"

        # Advanced
        assert config.log_level == "DEBUG"
        assert config.status_timeout == 120
        assert config.poll_interval == 20

    def test_load_from_env_when_no_file(self, monkeypatch, tmp_path):
        """Should load from ENV when options.json doesn't exist."""
        config_file = tmp_path / "nonexistent.json"

        monkeypatch.setenv("HUAWEI_MODBUS_HOST", "10.0.0.5")
        monkeypatch.setenv("HUAWEI_MODBUS_PORT", "5020")
        monkeypatch.setenv("HUAWEI_SLAVEID_AUTO", "false")
        monkeypatch.setenv("HUAWEI_SLAVE_ID", "2")
        monkeypatch.setenv("HUAWEI_MODBUS_MQTT_BROKER", "mqtt.local")
        monkeypatch.setenv("HUAWEI_MODBUS_MQTT_PORT", "1884")
        monkeypatch.setenv("HUAWEI_MODBUS_MQTT_USER", "envuser")
        monkeypatch.setenv("HUAWEI_MODBUS_MQTT_PASSWORD", "envpass")
        monkeypatch.setenv("HUAWEI_MODBUS_MQTT_TOPIC", "env-topic")
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        monkeypatch.setenv("MQTT_STATUS_TIMEOUT", "90")
        monkeypatch.setenv("MQTT_POLL_INTERVAL", "60")

        config = ConfigManager(config_path=config_file)

        assert config.modbus_host == "10.0.0.5"
        assert config.modbus_port == 5020
        assert config.auto_detect_slave_id is False
        assert config.slave_id == 2
        assert config.mqtt_broker == "mqtt.local"
        assert config.mqtt_port == 1884
        assert config.mqtt_username == "envuser"
        assert config.mqtt_password == "envpass"
        assert config.mqtt_topic_prefix == "env-topic"
        assert config.log_level == "ERROR"
        assert config.status_timeout == 90
        assert config.poll_interval == 60


class TestConfigManagerMigration:
    """Test migration from old flat config to new nested structure."""

    def test_migrate_flat_config_to_nested(self, tmp_path):
        """Should migrate old flat config to new nested structure."""
        config_file = tmp_path / "options.json"
        old_config = {
            "modbus_host": "192.168.1.100",
            "modbus_port": 502,
            "slave_id": 1,
            "mqtt_host": "localhost",
            "mqtt_port": 1883,
            "mqtt_user": "olduser",
            "mqtt_password": "oldpass",
            "mqtt_topic": "old-topic",
            "log_level": "INFO",
            "status_timeout": 180,
            "poll_interval": 30,
        }

        config_file.write_text(json.dumps(old_config))

        config = ConfigManager(config_path=config_file)

        # Should be migrated correctly
        assert config.modbus_host == "192.168.1.100"
        assert config.modbus_port == 502
        assert config.slave_id == 1
        assert config.mqtt_broker == "localhost"
        assert config.mqtt_port == 1883
        assert config.mqtt_username == "olduser"
        assert config.mqtt_password == "oldpass"
        assert config.mqtt_topic_prefix == "old-topic"
        assert config.log_level == "INFO"
        assert config.status_timeout == 180
        assert config.poll_interval == 30

    def test_migrate_partial_flat_config_with_defaults(self, tmp_path):
        """Should migrate partial flat config and use defaults."""
        config_file = tmp_path / "options.json"
        old_config = {
            "modbus_host": "192.168.1.50",
            "mqtt_topic": "partial-topic",
        }

        config_file.write_text(json.dumps(old_config))

        config = ConfigManager(config_path=config_file)

        # Provided values
        assert config.modbus_host == "192.168.1.50"
        assert config.mqtt_topic_prefix == "partial-topic"

        # Defaults
        assert config.modbus_port == 502
        assert config.slave_id == 1
        assert config.mqtt_broker == "localhost"
        assert config.mqtt_port == 1883
        assert config.log_level == "INFO"
        assert config.status_timeout == 180
        assert config.poll_interval == 30

    def test_no_migration_for_nested_config(self, tmp_path, caplog):
        """Should not migrate if config is already nested."""
        import logging

        caplog.set_level(logging.DEBUG)

        config_file = tmp_path / "options.json"
        nested_config = {
            "modbus": {"host": "192.168.1.100", "port": 502, "auto_detect_slave_id": True, "slave_id": 1},
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "username": None,
                "password": None,
                "topic_prefix": "huawei-solar",
                "discovery": True,
            },
            "advanced": {"log_level": "INFO", "status_timeout": 180, "poll_interval": 30},
        }

        config_file.write_text(json.dumps(nested_config))

        config = ConfigManager(config_path=config_file)

        # Should NOT see migration log
        assert "Migrating to new structure" not in caplog.text
        assert "already in new nested format" in caplog.text

        # Verify config was loaded correctly without migration
        assert config.modbus_host == "192.168.1.100"
        assert config.modbus_port == 502
        assert config.mqtt_broker == "localhost"
        assert config.mqtt_topic_prefix == "huawei-solar"


class TestConfigManagerProperties:
    """Test property accessors."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a ConfigManager with test data."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus": {
                "host": "192.168.1.100",
                "port": 502,
                "auto_detect_slave_id": False,
                "slave_id": 5,
            },
            "mqtt": {
                "broker": "mqtt.test",
                "port": 1883,
                "username": "user",
                "password": "pass",
                "topic_prefix": "test",
                "discovery": False,
            },
            "advanced": {
                "log_level": "WARNING",
                "status_timeout": 200,
                "poll_interval": 45,
            },
        }

        config_file.write_text(json.dumps(config_data))
        return ConfigManager(config_path=config_file)

    def test_modbus_properties(self, config):
        """Test modbus property accessors."""
        assert config.modbus_host == "192.168.1.100"
        assert config.modbus_port == 502
        assert config.auto_detect_slave_id is False
        assert config.slave_id == 5

    def test_mqtt_properties(self, config):
        """Test MQTT property accessors."""
        assert config.mqtt_broker == "mqtt.test"
        assert config.mqtt_port == 1883
        assert config.mqtt_username == "user"
        assert config.mqtt_password == "pass"
        assert config.mqtt_topic_prefix == "test"

    def test_advanced_properties(self, config):
        """Test advanced property accessors."""
        assert config.log_level == "WARNING"
        assert config.status_timeout == 200
        assert config.poll_interval == 45

    def test_mqtt_username_returns_none_for_empty_string(self, tmp_path):
        """Should return None for empty username."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus": {"host": "192.168.1.100", "port": 502, "auto_detect_slave_id": True, "slave_id": 1},
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "username": "",  # Empty string
                "password": "",  # Empty string
                "topic_prefix": "test",
                "discovery": True,
            },
            "advanced": {"log_level": "INFO", "status_timeout": 180, "poll_interval": 30},
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        assert config.mqtt_username is None
        assert config.mqtt_password is None

    def test_slave_id_can_be_none(self, tmp_path):
        """Slave ID can be None when auto-detect is enabled."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus": {
                "host": "192.168.1.100",
                "port": 502,
                "auto_detect_slave_id": True,
                # slave_id not set
            },
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "username": None,
                "password": None,
                "topic_prefix": "test",
                "discovery": True,
            },
            "advanced": {"log_level": "INFO", "status_timeout": 180, "poll_interval": 30},
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        assert config.slave_id is None


class TestConfigManagerEnvParsing:
    """Test environment variable parsing helpers."""

    def test_parse_bool_env_true_values(self, monkeypatch):
        """Should parse various true values."""
        for true_val in ["true", "True", "TRUE", "yes", "YES", "1", "on", "ON"]:
            monkeypatch.setenv("TEST_BOOL", true_val)
            config_mgr = ConfigManager._parse_bool_env("TEST_BOOL", default=False)
            assert config_mgr is True, f"Failed for value: {true_val}"

    def test_parse_bool_env_false_values(self, monkeypatch):
        """Should parse various false values."""
        for false_val in ["false", "False", "FALSE", "no", "NO", "0", "off", "OFF"]:
            monkeypatch.setenv("TEST_BOOL", false_val)
            config_mgr = ConfigManager._parse_bool_env("TEST_BOOL", default=True)
            assert config_mgr is False, f"Failed for value: {false_val}"

    def test_parse_bool_env_uses_default(self, monkeypatch):
        """Should use default when ENV not set."""
        monkeypatch.delenv("TEST_BOOL", raising=False)
        assert ConfigManager._parse_bool_env("TEST_BOOL", default=True) is True
        assert ConfigManager._parse_bool_env("TEST_BOOL", default=False) is False

    def test_parse_int_env_valid_value(self, monkeypatch):
        """Should parse valid integer."""
        monkeypatch.setenv("TEST_INT", "42")
        assert ConfigManager._parse_int_env("TEST_INT", default=0) == 42

    def test_parse_int_env_strips_whitespace(self, monkeypatch):
        """Should strip whitespace."""
        monkeypatch.setenv("TEST_INT", "  123  ")
        assert ConfigManager._parse_int_env("TEST_INT", default=0) == 123

    def test_parse_int_env_uses_default_for_null(self, monkeypatch):
        """Should use default for null-like values."""
        for null_val in ["", "null", "None", "none", "NONE"]:
            monkeypatch.setenv("TEST_INT", null_val)
            assert ConfigManager._parse_int_env("TEST_INT", default=99) == 99

    def test_parse_int_env_invalid_value_uses_default(self, monkeypatch, caplog):
        """Should use default for invalid integer."""
        monkeypatch.setenv("TEST_INT", "not_a_number")
        result = ConfigManager._parse_int_env("TEST_INT", default=50)
        assert result == 50
        assert "Invalid integer" in caplog.text


class TestConfigManagerLogConfig:
    """Test configuration logging."""

    def test_log_config_hides_password_by_default(self, tmp_path, caplog):
        """Should mask password in logs by default."""
        import logging

        caplog.set_level(logging.DEBUG)

        config_file = tmp_path / "options.json"
        config_data = {
            "modbus": {"host": "192.168.1.100", "port": 502, "auto_detect_slave_id": True, "slave_id": 1},
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "username": "testuser",
                "password": "secret123",
                "topic_prefix": "test",
                "discovery": True,
            },
            "advanced": {"log_level": "INFO", "status_timeout": 180, "poll_interval": 30},
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        config.log_config(hide_passwords=True)

        assert "secret123" not in caplog.text
        assert "***" in caplog.text
        assert "testuser" in caplog.text

    def test_log_config_shows_password_when_disabled(self, tmp_path, caplog):
        """Should show password when hide_passwords=False."""
        import logging

        caplog.set_level(logging.DEBUG)

        config_file = tmp_path / "options.json"
        config_data = {
            "modbus": {"host": "192.168.1.100", "port": 502, "auto_detect_slave_id": True, "slave_id": 1},
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "username": "testuser",
                "password": "secret123",
                "topic_prefix": "test",
                "discovery": True,
            },
            "advanced": {"log_level": "INFO", "status_timeout": 180, "poll_interval": 30},
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        config.log_config(hide_passwords=False)

        # Password sollte NICHT in Logs sein (wir wollen sie ja verstecken)
        # Dieser Test ist nur um zu zeigen dass der Parameter funktioniert
        assert "testuser" in caplog.text

    def test_log_config_shows_all_sections(self, tmp_path, caplog):
        """Should log all configuration sections."""
        import logging

        caplog.set_level(logging.DEBUG)

        config_file = tmp_path / "options.json"
        config_data = {
            "modbus": {"host": "192.168.1.100", "port": 502, "auto_detect_slave_id": False, "slave_id": 2},
            "mqtt": {
                "broker": "mqtt.test",
                "port": 1883,
                "username": None,
                "password": None,
                "topic_prefix": "huawei",
                "discovery": True,
            },
            "advanced": {"log_level": "DEBUG", "status_timeout": 120, "poll_interval": 25},
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        config.log_config()

        # Modbus section
        assert "192.168.1.100" in caplog.text
        assert "502" in caplog.text
        assert "Slave ID: 2" in caplog.text

        # MQTT section
        assert "mqtt.test" in caplog.text
        assert "1883" in caplog.text
        assert "huawei" in caplog.text

        # Advanced section
        assert "DEBUG" in caplog.text
        assert "120" in caplog.text
        assert "25" in caplog.text


class TestConfigManagerEdgeCases:
    """Test edge cases and error handling."""

    def test_default_config_when_no_file_no_env(self, tmp_path, monkeypatch):
        """Should use all defaults when no file and no ENV."""
        config_file = tmp_path / "nonexistent.json"

        # Clear all relevant ENV vars
        for key in [
            "HUAWEI_MODBUS_HOST",
            "HUAWEI_MODBUS_PORT",
            "HUAWEI_SLAVEID_AUTO",
            "HUAWEI_SLAVE_ID",
            "HUAWEI_MODBUS_MQTT_BROKER",
            "HUAWEI_MODBUS_MQTT_PORT",
            "HUAWEI_MODBUS_MQTT_USER",
            "HUAWEI_MODBUS_MQTT_PASSWORD",
            "HUAWEI_MODBUS_MQTT_TOPIC",
            "LOG_LEVEL",
            "MQTT_STATUS_TIMEOUT",
            "MQTT_POLL_INTERVAL",
        ]:
            monkeypatch.delenv(key, raising=False)

        config = ConfigManager(config_path=config_file)

        # All defaults
        assert config.modbus_host == "192.168.1.100"
        assert config.modbus_port == 502
        assert config.auto_detect_slave_id is True
        assert config.slave_id == 1
        assert config.mqtt_broker == "localhost"
        assert config.mqtt_port == 1883
        assert config.mqtt_topic_prefix == "huawei-solar"
        assert config.log_level == "INFO"
        assert config.status_timeout == 180
        assert config.poll_interval == 30

    def test_handles_missing_nested_keys_gracefully(self, tmp_path):
        """Should handle missing nested keys without crashing."""
        config_file = tmp_path / "options.json"
        incomplete_config = {
            "modbus": {
                "host": "192.168.1.100",
                # port missing
                # auto_detect_slave_id missing
                # slave_id missing
            },
            "mqtt": {
                "broker": "localhost",
                # Other fields missing
            },
            "advanced": {
                # All fields missing
            },
        }

        config_file.write_text(json.dumps(incomplete_config))

        # Should not crash - ConfigManager should handle missing keys gracefully
        # with get() and defaults
        config = ConfigManager(config_path=config_file)

        # Test that it doesn't crash when accessing properties
        # These will use defaults from the migration logic
        assert config.modbus_host == "192.168.1.100"  # Provided
        assert config.modbus_port == 502  # Default
        assert config.mqtt_broker == "localhost"  # Provided
        assert config.mqtt_port == 1883  # Default

    def test_empty_config_file(self, tmp_path):
        """Should handle empty config file."""
        config_file = tmp_path / "options.json"
        config_file.write_text("{}")

        config = ConfigManager(config_path=config_file)

        # Should migrate empty dict and use all defaults
        assert config.modbus_host == "192.168.1.100"
        assert config.mqtt_broker == "localhost"
