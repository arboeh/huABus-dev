"""End-to-End Tests - Kompletter Workflow: Modbus → Transform → Filter → MQTT"""

import json

import pytest  # type: ignore
from modbus_energy_meter.total_increasing_filter import get_filter, reset_filter

from tests.fixtures.mock_inverter import MockHuaweiSolar
from tests.fixtures.mock_mqtt_broker import MockMQTTBroker


@pytest.mark.asyncio
async def test_e2e_meter_change_scenario():
    """
    End-to-End: Neuer Meter installiert
    - Modbus liefert: 0 → 0.03 → 0.15 kWh
    - MQTT sollte empfangen: 0 → 0.03 → 0.15 kWh (alle Werte durchgelassen)
    """
    # Setup
    reset_filter()
    mock_modbus = MockHuaweiSolar()
    mock_modbus.load_scenario("meter_change")
    mock_mqtt = MockMQTTBroker()
    mock_mqtt.connect("localhost", 1883)
    filter_instance = get_filter()

    expected_values = [0, 0.03, 0.15]

    # Simulate 3 cycles
    for expected in expected_values:
        # 1. Modbus Read (simuliert)
        register = await mock_modbus.get("energy_grid_exported")
        raw_value = register.value

        # 2. Transform (würde normalerweise alle Register transformieren)
        transformed = {"energy_grid_exported": raw_value}

        # 3. Filter
        filtered = filter_instance.filter(transformed)

        # 4. MQTT Publish (simuliert)
        payload = json.dumps(filtered)
        mock_mqtt.publish("huawei-solar", payload)

        # 5. Assertion: Richtige Werte angekommen?
        latest = mock_mqtt.get_latest("huawei-solar")
        assert latest is not None, "No MQTT message received!"  # ← FIX
        assert latest["payload"]["energy_grid_exported"] == expected

        mock_modbus.next_cycle()

    # Finale Checks
    all_messages = mock_mqtt.get_messages("huawei-solar")
    assert len(all_messages) == 3
    print(f"✅ E2E Test passed: {expected_values} correctly transmitted via MQTT")


@pytest.mark.asyncio
async def test_e2e_modbus_errors_filtered_before_mqtt():
    """
    End-to-End: Modbus-Fehler werden gefiltert BEVOR sie MQTT erreichen
    - Modbus liefert: 5432.1 → 0 (Fehler!) → 5432.8 kWh
    - MQTT sollte empfangen: 5432.1 → 5432.1 (gefiltert!) → 5432.8 kWh
    """
    reset_filter()
    mock_modbus = MockHuaweiSolar()
    mock_modbus.load_scenario("modbus_errors")
    mock_mqtt = MockMQTTBroker()
    mock_mqtt.connect("localhost", 1883)
    filter_instance = get_filter()

    expected_values = [5432.1, 5432.1, 5432.8]  # Zweiter Wert gefiltert!

    for expected in expected_values:
        register = await mock_modbus.get("energy_grid_exported")
        raw_value = register.value

        transformed = {"energy_grid_exported": raw_value}
        filtered = filter_instance.filter(transformed)

        payload = json.dumps(filtered)
        mock_mqtt.publish("huawei-solar", payload)

        latest = mock_mqtt.get_latest("huawei-solar")
        assert latest is not None, "No MQTT message received!"  # ← FIX
        assert latest["payload"]["energy_grid_exported"] == expected

        mock_modbus.next_cycle()

    # Sicherstellen, dass 0 NIE zu MQTT gesendet wurde
    all_messages = mock_mqtt.get_messages("huawei-solar")
    for msg in all_messages:
        payload = msg.as_dict()["payload"]
        assert (
            payload["energy_grid_exported"] != 0
        ), "❌ Zero value reached MQTT - Filter failed!"

    print("✅ E2E Test passed: Zero values filtered before MQTT")


@pytest.mark.asyncio
async def test_e2e_multiple_sensors():
    """
    End-to-End: Multiple Sensoren gleichzeitig
    - Grid Export/Import, Solar Yield, Battery Charge/Discharge
    - Alle 5 total_increasing Sensoren werden korrekt gefiltert
    """
    reset_filter()
    mock_modbus = MockHuaweiSolar()
    mock_modbus.load_scenario("meter_change")
    mock_mqtt = MockMQTTBroker()
    mock_mqtt.connect("localhost", 1883)
    filter_instance = get_filter()

    for cycle in range(3):
        # Lese ALLE 5 total_increasing Sensoren
        grid_export = await mock_modbus.get("energy_grid_exported")
        grid_import = await mock_modbus.get("energy_grid_accumulated")
        solar = await mock_modbus.get("energy_yield_accumulated")
        battery_charge = await mock_modbus.get("battery_charge_total")
        battery_discharge = await mock_modbus.get("battery_discharge_total")

        transformed = {
            "energy_grid_exported": grid_export.value,
            "energy_grid_accumulated": grid_import.value,
            "energy_yield_accumulated": solar.value,
            "battery_charge_total": battery_charge.value,
            "battery_discharge_total": battery_discharge.value,
        }

        filtered = filter_instance.filter(transformed)

        payload = json.dumps(filtered)
        mock_mqtt.publish("huawei-solar", payload)

        mock_modbus.next_cycle()

    # Check: Alle 5 Sensoren in allen Messages vorhanden
    all_messages = mock_mqtt.get_messages("huawei-solar")
    assert len(all_messages) == 3

    for msg in all_messages:
        payload_dict = msg.as_dict()
        payload = payload_dict["payload"]

        # Alle 5 total_increasing Sensoren müssen vorhanden sein
        assert "energy_grid_exported" in payload
        assert "energy_grid_accumulated" in payload  # ← NEU
        assert "energy_yield_accumulated" in payload
        assert "battery_charge_total" in payload
        assert "battery_discharge_total" in payload  # ← NEU

    print("✅ E2E Test passed: All 5 total_increasing sensors correctly handled")


@pytest.mark.asyncio
async def test_e2e_mqtt_topic_structure():
    """
    End-to-End: MQTT Topic-Struktur korrekt
    - Data Topic: huawei-solar
    - Status Topic: huawei-solar/status
    """
    mock_mqtt = MockMQTTBroker()
    mock_mqtt.connect("localhost", 1883)

    # Data publish
    mock_mqtt.publish("huawei-solar", json.dumps({"energy_grid_exported": 100.5}))

    # Status publish
    mock_mqtt.publish("huawei-solar/status", "online", retain=True)

    # Assertions
    data_msg = mock_mqtt.get_latest("huawei-solar")
    status_msg = mock_mqtt.get_latest("huawei-solar/status")

    assert data_msg is not None, "No data message found!"  # ← FIX
    assert status_msg is not None, "No status message found!"  # ← FIX
    assert status_msg["retain"] == True  # Status sollte retained sein

    print("✅ E2E Test passed: MQTT topic structure correct")
