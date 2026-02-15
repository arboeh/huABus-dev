# huawei_solar_modbus_mqtt\bridge\slave_detector.py

"""Auto-detection of Modbus Slave ID for Huawei inverters."""

import asyncio

from huawei_solar import AsyncHuaweiSolar

from .logging_utils import get_logger

logger = get_logger("huawei.slave_detector")


KNOWN_SLAVE_IDS = [1, 2, 100]
"""Common Slave IDs in order of probability."""

TEST_REGISTER = "model_name"
"""Simple register to test connectivity."""

DETECTION_TIMEOUT = 5
"""Timeout per Slave ID attempt in seconds."""


async def detect_slave_id(host: str, port: int = 502, timeout: int = DETECTION_TIMEOUT) -> int | None:
    """
    Auto-detect Modbus Slave ID for Huawei inverter.

    Tries common Slave IDs (1, 2, 100) and returns the first working one.

    Args:
        host: Inverter IP address
        port: Modbus TCP port (default 502)
        timeout: Timeout per attempt in seconds (default 5)

    Returns:
        Detected Slave ID (0-247) or None if detection failed

    Example:
        >>> slave_id = await detect_slave_id("192.168.1.100")
        >>> if slave_id:
        ...     print(f"Found Slave ID: {slave_id}")
    """
    logger.info(f"🔍 Auto-detecting Slave ID for {host}:{port}...")

    for slave_id in KNOWN_SLAVE_IDS:
        logger.debug(f"Trying Slave ID {slave_id}...")

        if await _test_slave_id(host, port, slave_id, timeout):
            logger.info(f"🕵️‍♀️ Auto-detected Slave ID: {slave_id}")
            return slave_id

        logger.debug(f"Slave ID {slave_id} failed")

    logger.error(f"❌ Auto-detection failed! Tried: {KNOWN_SLAVE_IDS}")
    return None


async def _test_slave_id(host: str, port: int, slave_id: int, timeout: int) -> bool:
    """
    Test if specific Slave ID works.

    Args:
        host: Inverter IP address
        port: Modbus TCP port
        slave_id: Slave ID to test
        timeout: Timeout in seconds

    Returns:
        True if Slave ID works, False otherwise
    """
    client = None

    try:
        # Create client with timeout
        client = await asyncio.wait_for(
            AsyncHuaweiSolar.create(
                host=host,
                port=port,
                slave_id=slave_id,
            ),
            timeout=timeout,
        )

        # Try to read test register
        result = await asyncio.wait_for(client.get(TEST_REGISTER), timeout=timeout)

        # Success if we got a value
        if result and result.value:
            logger.debug(f"Slave ID {slave_id} works! Model: {result.value}")
            return True

    except TimeoutError:
        logger.debug(f"Slave ID {slave_id} timed out")
    except Exception as e:
        logger.debug(f"Slave ID {slave_id} error: {e}")
    finally:
        # Always cleanup
        if client:
            try:
                await client.stop()
            except Exception:
                pass

    return False


class SlaveDetector:
    """
    Stateful Slave ID detector.

    Use this if you need more control over detection process.
    For simple usage, use detect_slave_id() function instead.
    """

    def __init__(self, host: str, port: int = 502):
        """
        Initialize detector.

        Args:
            host: Inverter IP address
            port: Modbus TCP port (default 502)
        """
        self.host = host
        self.port = port

    async def detect(self, timeout: int = DETECTION_TIMEOUT) -> int | None:
        """
        Detect Slave ID.

        Args:
            timeout: Timeout per attempt in seconds

        Returns:
            Detected Slave ID or None
        """
        return await detect_slave_id(self.host, self.port, timeout)
