# tests/test_config_manager.py

"""Tests for ConfigManager."""

import json

import pytest
from bridge.config_manager import ConfigManager


class TestConfigManagerLoading:
    """Test configuration loading from different sources."""

    def test_load_from_file_flat_structure(self, tmp_path):
        """Should load flat config from options.json."""
        config_file = tmp_path / "options.json"
        config_data = {
            # Modbus (flat)
            "modbus_host": "192.168.1.200",
            "modbus_port": 502,
            "modbus_auto_detect_slave_id": True,
            "modbus_slave_id": 1,
            # MQTT (flat)
            "mqtt_broker": "mqtt.example.com",
            "mqtt_port": 1883,
            "mqtt_username": "testuser",
            "mqtt_password": "testpass",
            "mqtt_topic_prefix": "test-topic",
            # Advanced (flat)
            "log_level": "DEBUG",
            "status_timeout": 120,
            "poll_interval": 20,
        }

        config_file.write_text(json.dumps(config_data))

        config = ConfigManager(config_path=config_file)

        # Modbus
        assert config.modbus_host == "192.168.1.200"
        assert config.modbus_port == 502
        assert config.modbus_auto_detect_slave_id is True
        assert config.modbus_slave_id == 1

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
        monkeypatch.setenv("HUAWEI_LOG_LEVEL", "ERROR")
        monkeypatch.setenv("HUAWEI_STATUS_TIMEOUT", "90")
        monkeypatch.setenv("HUAWEI_POLL_INTERVAL", "60")

        config = ConfigManager(config_path=config_file)

        assert config.modbus_host == "10.0.0.5"
        assert config.modbus_port == 5020
        assert config.modbus_auto_detect_slave_id is False
        assert config.modbus_slave_id == 2
        assert config.mqtt_broker == "mqtt.local"
        assert config.mqtt_port == 1884
        assert config.mqtt_username == "envuser"
        assert config.mqtt_password == "envpass"
        assert config.mqtt_topic_prefix == "env-topic"
        assert config.log_level == "ERROR"
        assert config.status_timeout == 90
        assert config.poll_interval == 60


class TestConfigManagerProperties:
    """Test property accessors."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a ConfigManager with test data."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "modbus_port": 502,
            "modbus_auto_detect_slave_id": False,
            "modbus_slave_id": 5,
            "mqtt_broker": "mqtt.test",
            "mqtt_port": 1883,
            "mqtt_username": "user",
            "mqtt_password": "pass",
            "mqtt_topic_prefix": "test",
            "log_level": "WARNING",
            "status_timeout": 200,
            "poll_interval": 45,
        }

        config_file.write_text(json.dumps(config_data))
        return ConfigManager(config_path=config_file)

    def test_modbus_properties(self, config):
        """Test modbus property accessors."""
        assert config.modbus_host == "192.168.1.100"
        assert config.modbus_port == 502
        assert config.modbus_auto_detect_slave_id is False
        assert config.modbus_slave_id == 5

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
            "modbus_host": "192.168.1.100",
            "modbus_port": 502,
            "modbus_auto_detect_slave_id": True,
            "modbus_slave_id": 1,
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mqtt_username": "",  # Empty string
            "mqtt_password": "",  # Empty string
            "mqtt_topic_prefix": "test",
            "log_level": "INFO",
            "status_timeout": 180,
            "poll_interval": 30,
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        assert config.mqtt_username is None
        assert config.mqtt_password is None


class TestConfigManagerValidation:
    """Test configuration validation."""

    def test_validate_valid_config(self, tmp_path):
        """Should validate a correct config without errors."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "modbus_port": 502,
            "modbus_auto_detect_slave_id": True,
            "modbus_slave_id": 1,
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mqtt_topic_prefix": "test",
            "log_level": "INFO",
            "status_timeout": 180,
            "poll_interval": 30,
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        errors = config.validate()
        assert len(errors) == 0

    def test_validate_missing_required_fields(self, tmp_path):
        """Should detect empty required fields."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "",  # LEER statt fehlend!
            "mqtt_broker": "",  # LEER!
            "mqtt_topic_prefix": "",  # LEER!
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        errors = config.validate()
        assert len(errors) >= 3  # Mindestens 3 Fehler
        # Prüfe dass die Errors zu leeren Strings gehören
        error_text = " ".join(errors)
        assert "required" in error_text.lower()

    def test_validate_invalid_port_ranges(self, tmp_path):
        """Should detect invalid port numbers."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "modbus_port": 99999,  # Invalid!
            "mqtt_broker": "localhost",
            "mqtt_port": 0,  # Invalid!
            "mqtt_topic_prefix": "test",
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        errors = config.validate()
        assert len(errors) >= 2
        assert any("modbus_port" in err for err in errors)
        assert any("mqtt_port" in err for err in errors)

    def test_validate_invalid_log_level(self, tmp_path):
        """Should detect invalid log level."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "mqtt_broker": "localhost",
            "mqtt_topic_prefix": "test",
            "log_level": "INVALID",  # Not in list!
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        errors = config.validate()
        assert any("log_level" in err for err in errors)


class TestConfigManagerEnvParsing:
    """Test environment variable parsing helpers."""

    def test_parse_bool_env_true_values(self, monkeypatch):
        """Should parse various true values."""
        for true_val in ["true", "True", "TRUE", "yes", "YES", "1", "on", "ON"]:
            monkeypatch.setenv("TEST_BOOL", true_val)
            result = ConfigManager._parse_bool_env("TEST_BOOL", default=False)
            assert result is True, f"Failed for value: {true_val}"

    def test_parse_bool_env_false_values(self, monkeypatch):
        """Should parse various false values."""
        for false_val in ["false", "False", "FALSE", "no", "NO", "0", "off", "OFF"]:
            monkeypatch.setenv("TEST_BOOL", false_val)
            result = ConfigManager._parse_bool_env("TEST_BOOL", default=True)
            assert result is False, f"Failed for value: {false_val}"

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

    def test_parse_int_env_invalid_value_uses_default(self, monkeypatch, caplog):
        """Should use default for invalid integer."""
        monkeypatch.setenv("TEST_INT", "not_a_number")
        result = ConfigManager._parse_int_env("TEST_INT", default=50)
        assert result == 50
        assert "Invalid integer" in caplog.text


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
            "HUAWEI_LOG_LEVEL",
            "HUAWEI_STATUS_TIMEOUT",
            "HUAWEI_POLL_INTERVAL",
        ]:
            monkeypatch.delenv(key, raising=False)

        config = ConfigManager(config_path=config_file)

        # All defaults
        assert config.modbus_host == "192.168.1.100"
        assert config.modbus_port == 502
        assert config.modbus_auto_detect_slave_id is True
        assert config.modbus_slave_id == 1
        assert config.mqtt_broker == "core-mosquitto"
        assert config.mqtt_port == 1883
        assert config.mqtt_topic_prefix == "huawei-solar"
        assert config.log_level == "INFO"
        assert config.status_timeout == 180
        assert config.poll_interval == 30

    def test_partial_config_uses_defaults(self, tmp_path):
        """Should use defaults for missing keys."""
        config_file = tmp_path / "options.json"
        partial_config = {
            "modbus_host": "192.168.1.50",
            "mqtt_topic_prefix": "partial-topic",
        }

        config_file.write_text(json.dumps(partial_config))
        config = ConfigManager(config_path=config_file)

        # Provided values
        assert config.modbus_host == "192.168.1.50"
        assert config.mqtt_topic_prefix == "partial-topic"

        # Defaults
        assert config.modbus_port == 502
        assert config.mqtt_broker == "core-mosquitto"
        assert config.log_level == "INFO"

    def test_empty_config_file(self, tmp_path):
        """Should handle empty config file."""
        config_file = tmp_path / "options.json"
        config_file.write_text("{}")

        config = ConfigManager(config_path=config_file)

        # Should use all defaults
        assert config.modbus_host == "192.168.1.100"
        assert config.mqtt_broker == "core-mosquitto"

    def test_repr_does_not_leak_password(self, tmp_path):
        """__repr__ should not contain password."""
        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "mqtt_broker": "localhost",
            "mqtt_username": "user",
            "mqtt_password": "secret123",
            "mqtt_topic_prefix": "test",
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        repr_str = repr(config)
        assert "secret123" not in repr_str
        assert "192.168.1.100" in repr_str
        assert "localhost" in repr_str


class TestConfigManagerLogConfig:
    """Test configuration logging."""

    def test_log_config_hides_password_by_default(self, tmp_path, caplog):
        """Should mask password in logs by default."""
        import logging

        caplog.set_level(logging.INFO)

        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "modbus_port": 502,
            "modbus_auto_detect_slave_id": True,
            "modbus_slave_id": 1,
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mqtt_username": "testuser",
            "mqtt_password": "secret123",
            "mqtt_topic_prefix": "test",
            "log_level": "INFO",
            "status_timeout": 180,
            "poll_interval": 30,
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

        caplog.set_level(logging.INFO)

        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "modbus_port": 502,
            "modbus_auto_detect_slave_id": True,
            "modbus_slave_id": 1,
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mqtt_username": "testuser",
            "mqtt_password": "secret123",
            "mqtt_topic_prefix": "test",
            "log_level": "INFO",
            "status_timeout": 180,
            "poll_interval": 30,
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        config.log_config(hide_passwords=False)

        # Password sollte sichtbar sein wenn hide_passwords=False
        assert "secret123" in caplog.text
        assert "testuser" in caplog.text

    def test_log_config_shows_all_sections(self, tmp_path, caplog):
        """Should log all configuration sections."""
        import logging

        caplog.set_level(logging.INFO)

        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "modbus_port": 502,
            "modbus_auto_detect_slave_id": False,
            "modbus_slave_id": 2,
            "mqtt_broker": "mqtt.test",
            "mqtt_port": 1883,
            "mqtt_username": None,
            "mqtt_password": None,
            "mqtt_topic_prefix": "huawei",
            "log_level": "DEBUG",
            "status_timeout": 120,
            "poll_interval": 25,
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

    def test_log_config_shows_auth_none_when_no_credentials(self, tmp_path, caplog):
        """Should show 'Auth: None' when no username/password."""
        import logging

        caplog.set_level(logging.INFO)

        config_file = tmp_path / "options.json"
        config_data = {
            "modbus_host": "192.168.1.100",
            "mqtt_broker": "localhost",
            "mqtt_topic_prefix": "test",
            "mqtt_username": "",  # Empty = None
            "mqtt_password": "",
        }

        config_file.write_text(json.dumps(config_data))
        config = ConfigManager(config_path=config_file)

        config.log_config()

        assert "Auth: None" in caplog.text
