# tests/test_filter.py

from modbus_energy_meter.total_increasing_filter import (
    TotalIncreasingFilter,
)


def test_first_value_accepted():
    """Erster Wert wird immer akzeptiert (auch 0)"""
    filter_instance = TotalIncreasingFilter()

    # ✅ Mit Unterstrich!
    assert filter_instance._should_filter("energy_grid_exported", 0) is False
    assert filter_instance._should_filter("energy_yield_accumulated", 0.03) is False
    assert filter_instance._should_filter("battery_charge_total", 100.5) is False


def test_increasing_values_accepted():
    """Steigende Werte werden immer akzeptiert"""
    filter_instance = TotalIncreasingFilter()

    filter_instance._should_filter("energy_grid_exported", 0)
    assert filter_instance._should_filter("energy_grid_exported", 0.03) is False
    assert filter_instance._should_filter("energy_grid_exported", 0.15) is False


def test_equal_values_accepted():
    """Gleiche Werte werden akzeptiert"""
    filter_instance = TotalIncreasingFilter()

    filter_instance._should_filter("energy_grid_exported", 100.0)
    assert filter_instance._should_filter("energy_grid_exported", 100.0) is False


def test_drop_to_zero_filtered():
    """Drop von 5432 auf 0 wird gefiltert"""
    filter_instance = TotalIncreasingFilter()

    filter_instance._should_filter("energy_grid_exported", 5432.1)
    assert filter_instance._should_filter("energy_grid_exported", 0) is True

    # get_last_value ist auch private!
    assert filter_instance._last_values.get("energy_grid_exported") == 5432.1


def test_negative_values_filtered():
    """Negative Werte werden immer gefiltert"""
    filter_instance = TotalIncreasingFilter()

    filter_instance._should_filter("energy_grid_exported", 5432.1)
    assert filter_instance._should_filter("energy_grid_exported", -10) is True
    assert filter_instance._should_filter("energy_grid_exported", -0.5) is True


def test_non_energy_sensors_not_filtered():
    """Nicht-Energy-Sensoren werden nicht gefiltert"""
    filter_instance = TotalIncreasingFilter()

    filter_instance._should_filter("power_active", 5000)
    assert filter_instance._should_filter("power_active", 0) is False


def test_filter_statistics():
    """Filter-Statistik wird korrekt gezählt"""
    filter_instance = TotalIncreasingFilter()

    # ✅ NICHT _should_filter() nutzen, sondern filter()!
    # Setup: Erste Werte setzen
    filter_instance.filter({"energy_grid_exported": 5432.1})
    filter_instance.filter({"battery_charge_total": 4804.5})

    # Fehler provozieren (werden gefiltert)
    filter_instance.filter({"energy_grid_exported": 0})  # Gefiltert
    filter_instance.filter({"battery_charge_total": 0})  # Gefiltert
    filter_instance.filter({"energy_grid_exported": 0})  # Nochmal gefiltert

    stats = filter_instance.get_stats()
    assert stats["energy_grid_exported"] == 2
    assert stats["battery_charge_total"] == 1


def test_reset_clears_state():
    """Reset löscht alle gespeicherten Werte"""
    filter_instance = TotalIncreasingFilter()

    filter_instance._should_filter("energy_grid_exported", 5432.1)
    assert filter_instance._last_values.get("energy_grid_exported") == 5432.1

    filter_instance.reset()

    assert filter_instance._last_values.get("energy_grid_exported") is None
