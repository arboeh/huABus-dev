# tests\test_main.py

"""Tests for main module connection and retry logic."""

import os
from unittest.mock import AsyncMock, patch

import pytest  # type: ignore
from modbus_energy_meter.main import main
from modbus_energy_meter.total_increasing_filter import reset_filter


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    reset_filter()
    yield
    reset_filter()


@pytest.fixture
def mock_env():
    """Mock required environment variables."""
    env_vars = {
        "HUAWEI_MODBUS_MQTT_TOPIC": "test-topic",
        "HUAWEI_MODBUS_HOST": "192.168.1.100",
        "HUAWEI_MODBUS_PORT": "502",
        "HUAWEI_SLAVE_ID": "1",
        "HUAWEI_POLL_INTERVAL": "30",
        "HUAWEI_STATUS_TIMEOUT": "180",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.mark.asyncio
async def test_main_connection_retry_on_failure(mock_env):
    """Test that main() handles connection failures gracefully."""
    with (
        patch("modbus_energy_meter.main.AsyncHuaweiSolar.create") as mock_create,
        patch("modbus_energy_meter.main.connect_mqtt"),
        patch("modbus_energy_meter.main.disconnect_mqtt"),
        patch("modbus_energy_meter.main.publish_status"),
        patch("modbus_energy_meter.main.publish_discovery_configs"),
        patch("modbus_energy_meter.main.main_once"),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        # Connection fails
        mock_create.side_effect = ConnectionRefusedError("Connection refused")

        # Main should log error and return (not crash)
        await main()

        # Verify connection was attempted
        assert mock_create.call_count == 1


@pytest.mark.asyncio
async def test_main_graceful_shutdown(mock_env):
    """Test graceful shutdown on KeyboardInterrupt."""
    with (
        patch("modbus_energy_meter.main.AsyncHuaweiSolar.create") as mock_create,
        patch("modbus_energy_meter.main.connect_mqtt"),
        patch("modbus_energy_meter.main.disconnect_mqtt") as mock_disconnect,
        patch("modbus_energy_meter.main.publish_status") as mock_status,
        patch("modbus_energy_meter.main.publish_discovery_configs"),
        patch("modbus_energy_meter.main.main_once") as mock_once,
    ):
        mock_client = AsyncMock()
        mock_create.return_value = mock_client

        # Simulate KeyboardInterrupt during main loop
        mock_once.side_effect = KeyboardInterrupt()

        # Main should exit gracefully via asyncio.CancelledError handler
        try:
            await main()
        except KeyboardInterrupt:
            pass

        # Verify disconnect was called
        assert mock_disconnect.call_count >= 1

        # Verify status was set to offline
        assert any(call[0][0] == "offline" for call in mock_status.call_args_list)


@pytest.mark.asyncio
async def test_main_timeout_exception_triggers_reconnect(mock_env):
    """Test that timeout exception triggers filter reset and continues."""
    with (
        patch("modbus_energy_meter.main.AsyncHuaweiSolar.create") as mock_create,
        patch("modbus_energy_meter.main.connect_mqtt"),
        patch("modbus_energy_meter.main.publish_status") as mock_status,
        patch("modbus_energy_meter.main.publish_discovery_configs"),
        patch("modbus_energy_meter.main.main_once") as mock_once,
        patch("modbus_energy_meter.main.reset_filter") as mock_reset_filter,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_client = AsyncMock()
        mock_create.return_value = mock_client

        # First cycle times out, second cycle stops
        mock_once.side_effect = [
            TimeoutError("Connection timeout"),
            KeyboardInterrupt(),
        ]

        try:
            await main()
        except KeyboardInterrupt:
            pass

        # Verify filter was reset after timeout
        assert mock_reset_filter.call_count >= 1

        # Verify status was published as offline after timeout
        offline_calls = [
            call for call in mock_status.call_args_list if call[0][0] == "offline"
        ]
        assert len(offline_calls) >= 1

        # Verify sleep was called (retry delay)
        assert mock_sleep.call_count >= 1


@pytest.mark.asyncio
async def test_main_modbus_exception_handling(mock_env):
    """Test Modbus exception triggers filter reset and continues."""
    from pymodbus.exceptions import ModbusException

    with (
        patch("modbus_energy_meter.main.AsyncHuaweiSolar.create") as mock_create,
        patch("modbus_energy_meter.main.connect_mqtt"),
        patch("modbus_energy_meter.main.publish_status") as mock_status,
        patch("modbus_energy_meter.main.publish_discovery_configs"),
        patch("modbus_energy_meter.main.main_once") as mock_once,
        patch("modbus_energy_meter.main.reset_filter") as mock_reset_filter,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_client = AsyncMock()
        mock_create.return_value = mock_client

        # ModbusException then stop
        mock_once.side_effect = [
            ModbusException("Modbus read error"),
            KeyboardInterrupt(),
        ]

        try:
            await main()
        except KeyboardInterrupt:
            pass

        # Verify filter was reset
        assert mock_reset_filter.call_count >= 1

        # Verify offline status
        offline_calls = [
            call for call in mock_status.call_args_list if call[0][0] == "offline"
        ]
        assert len(offline_calls) >= 1
