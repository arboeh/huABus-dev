# tests\test_slave_detector.py

"""Tests for Auto Slave ID Detection."""

import logging
from unittest.mock import AsyncMock, patch

import pytest
from bridge.slave_detector import (
    KNOWN_SLAVE_IDS,
    _test_slave_id,
    detect_slave_id,
)


class TestSlaveDetection:
    """Test auto Slave ID detection."""

    @pytest.mark.asyncio
    async def test_detect_slave_id_finds_first_working(self):
        """Test detection finds first working Slave ID (1)."""

        async def mock_test(host, port, slave_id, timeout):
            # Only Slave ID 1 works
            return slave_id == 1

        with patch("bridge.slave_detector._test_slave_id", side_effect=mock_test):
            result = await detect_slave_id("192.168.1.100", 502)

            assert result == 1

    @pytest.mark.asyncio
    async def test_detect_slave_id_tries_all_ids(self):
        """Test detection tries all known IDs in order."""

        async def mock_test(host, port, slave_id, timeout):
            # Only Slave ID 100 works (last one)
            return slave_id == 100

        with patch("bridge.slave_detector._test_slave_id", side_effect=mock_test) as mock:
            result = await detect_slave_id("192.168.1.100", 502)

            assert result == 100
            # Verify all IDs were tried
            assert mock.call_count == len(KNOWN_SLAVE_IDS)

    @pytest.mark.asyncio
    async def test_detect_slave_id_returns_none_on_failure(self):
        """Test detection returns None if all IDs fail."""

        async def mock_test(host, port, slave_id, timeout):
            # All fail
            return False

        with patch("bridge.slave_detector._test_slave_id", side_effect=mock_test):
            result = await detect_slave_id("192.168.1.100", 502)

            assert result is None

    @pytest.mark.asyncio
    async def test_detect_slave_id_uses_custom_timeout(self):
        """Test detection uses provided timeout."""

        async def mock_test(host, port, slave_id, timeout):
            assert timeout == 10  # Custom timeout
            return slave_id == 1

        with patch("bridge.slave_detector._test_slave_id", side_effect=mock_test):
            result = await detect_slave_id("192.168.1.100", 502, timeout=10)

            assert result == 1


class TestSlaveIdTesting:
    """Test individual Slave ID testing."""

    @pytest.mark.asyncio
    async def test_test_slave_id_success(self):
        """Test successful Slave ID test."""

        mock_result = AsyncMock()
        mock_result.value = "SUN2000-6KTL-M1"

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_result

        with patch("bridge.slave_detector.AsyncHuaweiSolar.create") as mock_create:
            mock_create.return_value = mock_client

            result = await _test_slave_id("192.168.1.100", 502, 1, timeout=5)

            assert result is True
            mock_create.assert_called_once()
            mock_client.get.assert_called_once_with("model_name")
            mock_client.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_slave_id_timeout(self):
        """Test Slave ID test handles timeout."""

        with patch("bridge.slave_detector.AsyncHuaweiSolar.create") as mock_create:
            # Simulate timeout
            mock_create.side_effect = TimeoutError("Connection timeout")

            result = await _test_slave_id("192.168.1.100", 502, 1, timeout=1)

            assert result is False

    @pytest.mark.asyncio
    async def test_test_slave_id_connection_refused(self):
        """Test Slave ID test handles connection refused."""

        with patch("bridge.slave_detector.AsyncHuaweiSolar.create") as mock_create:
            # Simulate connection refused
            mock_create.side_effect = ConnectionRefusedError("Connection refused")

            result = await _test_slave_id("192.168.1.100", 502, 1, timeout=1)

            assert result is False

    @pytest.mark.asyncio
    async def test_test_slave_id_empty_response(self):
        """Test Slave ID test handles empty response."""

        mock_result = AsyncMock()
        mock_result.value = None  # Empty response

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_result

        with patch("bridge.slave_detector.AsyncHuaweiSolar.create") as mock_create:
            mock_create.return_value = mock_client

            result = await _test_slave_id("192.168.1.100", 502, 1, timeout=5)

            assert result is False
            mock_client.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_slave_id_cleanup_on_error(self):
        """Test cleanup happens even on error."""

        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Read error")

        with patch("bridge.slave_detector.AsyncHuaweiSolar.create") as mock_create:
            mock_create.return_value = mock_client

            result = await _test_slave_id("192.168.1.100", 502, 1, timeout=5)

            assert result is False
            # Cleanup should happen despite error
            mock_client.stop.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_detect_stops_after_first_success(self):
        """Test detection stops after finding working ID."""

        call_count = 0

        async def mock_test(host, port, slave_id, timeout):
            nonlocal call_count
            call_count += 1
            # First call (slave_id=1) succeeds
            return call_count == 1

        with patch("bridge.slave_detector._test_slave_id", side_effect=mock_test):
            result = await detect_slave_id("192.168.1.100", 502)

            assert result == KNOWN_SLAVE_IDS[0]  # First ID
            assert call_count == 1  # Only one attempt

    @pytest.mark.asyncio
    async def test_detect_with_different_port(self):
        """Test detection with non-standard port."""

        async def mock_test(host, port, slave_id, timeout):
            assert port == 5020  # Custom port
            return slave_id == 1

        with patch("bridge.slave_detector._test_slave_id", side_effect=mock_test):
            result = await detect_slave_id("192.168.1.100", 5020)

            assert result == 1

    @pytest.mark.asyncio
    async def test_detect_logs_attempts(self, caplog):
        """Test detection logs each attempt."""
        caplog.set_level(logging.INFO)  # ← Wichtig für "Auto-detecting..." Log

        with (
            patch("bridge.slave_detector.AsyncHuaweiSolar.create") as mock_create,
        ):
            # All attempts fail
            mock_create.side_effect = Exception("Connection failed")

            result = await detect_slave_id("192.168.1.100", 502)

            assert result is None
            # Check logs
            assert "Auto-detection failed" in caplog.text  # ← Warnung am Ende
            assert "[1, 2, 100]" in caplog.text  # ← Liste wird geloggt
