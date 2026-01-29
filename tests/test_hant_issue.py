"""
Tests für HANTs gemeldetes Problem:
Spikes in Utility Meter trotz Filter

GitHub Issue: #7
"""

import pytest  # type: ignore
from modbus_energy_meter.total_increasing_filter import get_filter, reset_filter

from tests.fixtures.mock_inverter import MockHuaweiSolar
from tests.fixtures.mock_mqtt_broker import MockMQTTBroker


@pytest.mark.asyncio
async def test_hant_addon_restart_scenario():
    """
    HANT's Problem: Add-on restart → Sensor unavailable → Returns with value

    Szenario:
    1. Normaler Betrieb: 5432.1 kWh
    2. Add-on restart → Filter reset
    3. Sensor kommt zurück: 5433.5 kWh

    Erwartung:
    - Filter akzeptiert 5433.5 als "first value" nach Reset
    - MQTT empfängt: 5432.1 → 5432.8 → 5433.5 → 5434.2 (kein Sprung!)
    - Utility Meter sollte keine Spikes sehen
    """
    # Setup
    reset_filter()
    mock_modbus = MockHuaweiSolar()
    mock_modbus.load_scenario("addon_restart")
    mock_mqtt = MockMQTTBroker()
    mock_mqtt.connect("localhost", 1883)
    filter_instance = get_filter()

    results = []

    # Cycle 0 + 1: Normaler Betrieb
    for _ in range(2):
        register = await mock_modbus.get("energy_grid_exported")
        value = register.value

        filtered_data = filter_instance.filter({"energy_grid_exported": value})
        mqtt_data = {"energy_grid_exported": filtered_data["energy_grid_exported"]}

        mock_mqtt.publish("huawei-solar", str(mqtt_data))
        results.append(mqtt_data["energy_grid_exported"])

        mock_modbus.next_cycle()

    # === SIMULIERE RESTART ===
    # In echtem System: Add-on wird neu gestartet
    # → Filter-Instanz wird neu erstellt
    # → last_values sind leer
    reset_filter()
    filter_instance = get_filter()  # Neue Instanz!

    # Cycle 2 + 3: Nach Restart
    for _ in range(2):
        register = await mock_modbus.get("energy_grid_exported")
        value = register.value

        filtered_data = filter_instance.filter({"energy_grid_exported": value})
        mqtt_data = {"energy_grid_exported": filtered_data["energy_grid_exported"]}

        mock_mqtt.publish("huawei-solar", str(mqtt_data))
        results.append(mqtt_data["energy_grid_exported"])

        mock_modbus.next_cycle()

    # Assertions
    assert results == [5432.1, 5432.8, 5433.5, 5434.2]

    # Prüfe: Keine großen Sprünge (> 10 kWh wäre unrealistisch in 30s)
    for i in range(1, len(results)):
        diff = abs(results[i] - results[i - 1])
        assert diff < 10.0, f"Unrealistic jump: {results[i-1]} → {results[i]} (+{diff})"

    print("✅ HANT Test: No spikes after restart")


@pytest.mark.asyncio
async def test_hant_overnight_shutdown():
    """
    HANT's Szenario: Add-on läuft nicht über Nacht, startet morgens

    Problem:
    - Abends: 5432.1 kWh
    - Über Nacht: Add-on aus (oder Inverter aus)
    - Morgens: 5435.8 kWh (Nacht-Einspeisung ist passiert)

    Erwartung:
    - Filter erkennt: Das ist ein normaler Anstieg, kein Reset
    - Utility Meter addiert: 5435.8 - 5432.1 = 3.7 kWh (korrekt!)
    """
    reset_filter()
    mock_modbus = MockHuaweiSolar()
    mock_modbus.load_scenario("startup_with_previous_value")
    mock_mqtt = MockMQTTBroker()
    mock_mqtt.connect("localhost", 1883)
    filter_instance = get_filter()

    # Abends: Letzter Wert vor Shutdown
    register = await mock_modbus.get("energy_grid_exported")
    evening_value = register.value

    filtered = filter_instance.filter({"energy_grid_exported": evening_value})
    mock_mqtt.publish("huawei-solar", str(filtered))

    # === SHUTDOWN ÜBER NACHT ===
    # Filter behält last_value NICHT (wird neu gestartet)
    reset_filter()
    filter_instance = get_filter()

    mock_modbus.next_cycle()

    # Morgens: Startup mit höherem Wert
    register = await mock_modbus.get("energy_grid_exported")
    morning_value = register.value

    filtered = filter_instance.filter({"energy_grid_exported": morning_value})
    mock_mqtt.publish("huawei-solar", str(filtered))

    # Assertions
    assert morning_value > evening_value, "Morning value should be higher"
    assert (
        filtered["energy_grid_exported"] == morning_value
    ), "Filter should accept higher value"

    # Prüfe: Differenz ist realistisch (< 50 kWh über Nacht)
    diff = morning_value - evening_value
    assert diff < 50.0, f"Unrealistic overnight increase: {diff} kWh"

    print(f"✅ HANT Test: Overnight increase {diff:.1f} kWh accepted")


@pytest.mark.asyncio
async def test_hant_intermittent_failures_dont_reach_mqtt():
    """
    HANT's Beobachtung: Filter summary zeigt "0 filtered", aber Spikes passieren

    Test: Simuliere mehrere Modbus-Fehler und prüfe:
    - Filter MUSS diese Fehler fangen
    - MQTT darf NIE eine 0 sehen
    - Filter summary MUSS > 0 filtered zeigen
    """
    reset_filter()
    mock_modbus = MockHuaweiSolar()
    mock_modbus.load_scenario("intermittent_modbus_failures")
    mock_mqtt = MockMQTTBroker()
    mock_mqtt.connect("localhost", 1883)
    filter_instance = get_filter()

    mqtt_values = []

    for cycle in range(6):
        register = await mock_modbus.get("energy_grid_exported")
        raw_value = register.value

        filtered = filter_instance.filter({"energy_grid_exported": raw_value})
        mqtt_value = filtered["energy_grid_exported"]

        mock_mqtt.publish("huawei-solar", str(filtered))
        mqtt_values.append(mqtt_value)

        mock_modbus.next_cycle()

    # KRITISCH: MQTT darf NIE eine 0 sehen!
    for val in mqtt_values:
        assert val != 0, f"❌ CRITICAL: Zero value reached MQTT! Values: {mqtt_values}"

    # Filter-Statistik prüfen
    stats = filter_instance.get_stats()
    filtered_count = stats.get("energy_grid_exported", 0)

    assert (
        filtered_count > 0
    ), f"❌ Filter should have filtered values, but stats show: {stats}"

    # Erwartete Werte: [5432.1, 5432.8, 5432.8 (gefiltert!), 5433.5, 5433.5 (gefiltert!), 5434.2]
    expected = [5432.1, 5432.8, 5432.8, 5433.5, 5433.5, 5434.2]
    assert mqtt_values == expected, f"Values don't match: {mqtt_values} vs {expected}"

    print(f"✅ HANT Test: {filtered_count} values filtered, none reached MQTT")


@pytest.mark.asyncio
async def test_hant_utility_meter_simulation():
    """
    Simuliert was HA Utility Meter sieht:
    - Werte über Midnight-Reset
    - Add-on Restart

    Prüft ob MQTT-Daten konsistent sind (keine Rückwärts-Sprünge)
    """
    reset_filter()
    mock_modbus = MockHuaweiSolar()
    mock_modbus.load_scenario("utility_meter_reset_simulation")
    mock_mqtt = MockMQTTBroker()
    mock_mqtt.connect("localhost", 1883)
    filter_instance = get_filter()

    mqtt_values = []
    timestamps = []

    for _ in range(3):
        register = await mock_modbus.get("energy_grid_exported")
        value = register.value

        filtered = filter_instance.filter({"energy_grid_exported": value})
        mqtt_values.append(filtered["energy_grid_exported"])

        # Simuliere Timestamp (würde in echtem System von transform kommen)
        timestamps.append(f"cycle_{len(mqtt_values)}")

        mock_modbus.next_cycle()

    # Prüfe: Werte steigen monoton (oder bleiben gleich)
    for i in range(1, len(mqtt_values)):
        assert (
            mqtt_values[i] >= mqtt_values[i - 1]
        ), f"❌ Value dropped: {mqtt_values[i-1]} → {mqtt_values[i]} at {timestamps[i]}"

    print(f"✅ HANT Test: Utility Meter simulation OK, values: {mqtt_values}")
