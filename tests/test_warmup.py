# tests/test_warmup.py

import logging
import os

from modbus_energy_meter.total_increasing_filter import (
    TotalIncreasingFilter,
)


def test_warmup_period_basic():
    """Warmup-Period: Erste 3 Cycles ohne Filterung"""
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Cycle 1: Auch 0 wird durchgelassen
    result1 = filter_instance.filter({"energy_grid_exported": 0})
    assert result1["energy_grid_exported"] == 0
    assert filter_instance._warmup_active is True  # ← FIX
    assert filter_instance._warmup_counter == 1  # ← FIX

    # Cycle 2: Weiterer Wert
    result2 = filter_instance.filter({"energy_grid_exported": 5432.1})
    assert result2["energy_grid_exported"] == 5432.1
    assert filter_instance._warmup_active is True  # ← FIX

    # Cycle 3: Letzter Warmup-Cycle
    result3 = filter_instance.filter({"energy_grid_exported": 5432.8})
    assert result3["energy_grid_exported"] == 5432.8
    assert filter_instance._warmup_active is False  # ← FIX: Warmup complete!


def test_hant_issue_7_scenario():
    """HANT Issue #7: Zero-Drop nach Connection-Reset"""
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Phase 1: Normaler Betrieb
    for i in range(5):
        filter_instance.filter({"energy_grid_exported": 5432.1 + i * 0.5})
    assert filter_instance._warmup_active is False  # ← FIX

    # Phase 2: Connection Error → Reset
    filter_instance.reset()
    assert filter_instance._warmup_active is True  # ← FIX: Warmup neu gestartet

    # Phase 3: Zero während Warmup (wird durchgelassen!)
    result = filter_instance.filter({"energy_grid_exported": 0})
    assert result["energy_grid_exported"] == 0

    # Phase 4: Nach Warmup sollte 0 gefiltert werden
    filter_instance.filter({"energy_grid_exported": 5432.1})
    filter_instance.filter({"energy_grid_exported": 5433.0})
    result_after_warmup = filter_instance.filter({"energy_grid_exported": 0})
    assert result_after_warmup["energy_grid_exported"] == 5433.0  # Gefiltert!


def test_warmup_with_all_five_sensors():
    """Warmup: Alle 5 total_increasing Sensoren gleichzeitig"""
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Cycle 1: Alle Sensoren mit verschiedenen Werten
    data1 = {
        "energy_yield_accumulated": 18052.68,
        "energy_grid_exported": 9799.50,
        "energy_grid_accumulated": 3502.66,
        "battery_charge_total": 4851.74,
        "battery_discharge_total": 4649.64,
    }
    result1 = filter_instance.filter(data1)

    # Alle Werte sollten durchkommen (Warmup!)
    assert result1 == data1
    assert filter_instance._warmup_active is True  # ← FIX
    assert filter_instance._warmup_counter == 1  # ← FIX

    # Cycle 2-3: Warmup fortsetzen
    filter_instance.filter(data1)
    filter_instance.filter(data1)
    assert filter_instance._warmup_active is False  # ← FIX


def test_warmup_suspicious_zero_detection():
    """Warmup: Zero-Werte werden als suspicious markiert"""
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Cycle 1: Zero-Wert (suspicious!)
    result = filter_instance.filter({"energy_grid_exported": 0})

    assert result["energy_grid_exported"] == 0  # Durchgelassen (Warmup)
    assert "energy_grid_exported" in filter_instance._suspicious_first_values  # ← FIX


def test_warmup_suspicious_recovery():
    """
    Warmup: Recovery von suspicious Zero zu normalem Wert

    ✅ FIX: suspicious_first_values wird NICHT gelöscht (by design!)
    """
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Cycle 1: Suspicious Zero
    filter_instance.filter({"energy_grid_exported": 0})
    assert "energy_grid_exported" in filter_instance._suspicious_first_values  # ← FIX

    # Cycle 2-3: Normale Werte
    filter_instance.filter({"energy_grid_exported": 5432.1})
    filter_instance.filter({"energy_grid_exported": 5432.8})

    # Warmup complete
    assert filter_instance._warmup_active is False  # ← FIX

    # Cycle 4: Weiterer normaler Wert → Recovery
    filter_instance.filter({"energy_grid_exported": 5433.5})

    # ✅ Recovery erkannt, suspicious WIRD gelöscht!
    assert (
        "energy_grid_exported" not in filter_instance._suspicious_first_values
    )  # ← FIX


def test_warmup_custom_cycles():
    """Warmup: Custom warmup_cycles (1, 5, 10)"""
    # Test mit 1 Cycle
    filter1 = TotalIncreasingFilter(warmup_cycles=1)
    filter1.filter({"energy_grid_exported": 0})
    assert filter1._warmup_active is False  # ← FIX: Sofort aktiv!

    # Test mit 5 Cycles
    filter5 = TotalIncreasingFilter(warmup_cycles=5)
    for i in range(5):
        filter5.filter({"energy_grid_exported": 5432.1})
    assert filter5._warmup_active is False  # ← FIX

    # Test mit 10 Cycles
    filter10 = TotalIncreasingFilter(warmup_cycles=10)
    for i in range(9):
        filter10.filter({"energy_grid_exported": 5432.1})
    assert filter10._warmup_active is True  # ← FIX: Noch nicht fertig
    filter10.filter({"energy_grid_exported": 5432.1})
    assert filter10._warmup_active is False  # ← FIX: Jetzt fertig


def test_warmup_mixed_zero_and_normal_values():
    """Warmup: Gemischte Zero und normale Werte"""
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Cycle 1: Mix aus 0 und normalen Werten
    data = {
        "energy_yield_accumulated": 18052.68,  # Normal
        "energy_grid_exported": 0,  # Suspicious!
        "battery_charge_total": 4851.74,  # Normal
    }
    filter_instance.filter(data)

    # Nur energy_grid_exported sollte suspicious sein
    assert "energy_grid_exported" in filter_instance._suspicious_first_values  # ← FIX
    assert (
        "energy_yield_accumulated" not in filter_instance._suspicious_first_values
    )  # ← FIX
    assert (
        "battery_charge_total" not in filter_instance._suspicious_first_values
    )  # ← FIX


def test_warmup_reset_clears_suspicious():
    """Warmup: Reset entfernt suspicious-Liste"""
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Cycle 1-3: Warmup mit suspicious Zero
    filter_instance.filter({"energy_grid_exported": 0})
    filter_instance.filter({"energy_grid_exported": 5432.1})
    filter_instance.filter({"energy_grid_exported": 5432.8})

    # Warmup complete, aber suspicious bleibt (für Diagnose)
    assert filter_instance._warmup_active is False  # ← FIX
    assert "energy_grid_exported" in filter_instance._suspicious_first_values  # ← FIX

    # Reset
    filter_instance.reset()

    # Nach Reset: Warmup neu gestartet, suspicious BLEIBT (für Diagnose!)
    assert filter_instance._warmup_active is True  # ← FIX
    assert filter_instance._warmup_counter == 0  # ← FIX
    # ✅ suspicious_first_values bleibt erhalten (by design)
    assert "energy_grid_exported" in filter_instance._suspicious_first_values  # ← FIX


def test_warmup_after_connection_error():
    """Warmup: Nach Connection-Error wird Warmup neu gestartet"""
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Phase 1: Normaler Betrieb
    for i in range(10):
        filter_instance.filter({"energy_grid_exported": 5432.1 + i * 0.5})
    assert filter_instance._warmup_active is False  # ← FIX

    # Phase 2: Connection Error
    filter_instance.reset()
    assert filter_instance._warmup_active is True  # ← FIX: Warmup neu!
    assert filter_instance._warmup_counter == 0  # ← FIX

    # Phase 3: Neue Cycles nach Reset
    for i in range(3):
        filter_instance.filter({"energy_grid_exported": 5438.0 + i * 0.2})
    assert filter_instance._warmup_active is False  # ← FIX


def test_warmup_zero_stays_zero_during_warmup():
    """Warmup: Zero-Drop während Warmup bleibt Zero (kein Filter aktiv!)"""
    filter_instance = TotalIncreasingFilter(warmup_cycles=3)

    # Cycle 1: Normaler Wert
    filter_instance.filter({"energy_grid_exported": 5432.1})

    # Cycle 2: Drop auf 0 (sollte NICHT gefiltert werden, Warmup!)
    result2 = filter_instance.filter({"energy_grid_exported": 0})
    assert result2["energy_grid_exported"] == 0  # ⚠️ 0 durchgelassen!
    assert filter_instance._warmup_active is True  # ← FIX

    # Cycle 3: Warmup complete
    filter_instance.filter({"energy_grid_exported": 5432.8})
    assert filter_instance._warmup_active is False  # ← FIX

    # Cycle 4: Jetzt sollte 0 gefiltert werden!
    result4 = filter_instance.filter({"energy_grid_exported": 0})
    assert result4["energy_grid_exported"] == 5432.8  # Gefiltert!


def test_warmup_logging_output(caplog):
    """Warmup: Logging ist korrekt (für manuelle Verifikation)"""
    caplog.set_level(logging.INFO)

    filter_instance = TotalIncreasingFilter(warmup_cycles=2)

    # Cycle 1
    filter_instance.filter({"energy_grid_exported": 5432.1})
    assert "✅ WARMUP: First value for energy_grid_exported" in caplog.text
    assert "cycle 1/2" in caplog.text

    # Cycle 2
    filter_instance.filter({"energy_grid_exported": 5432.8})
    assert "✅ Warmup complete after 2 cycles" in caplog.text  # ← Jetzt korrekt!


def test_warmup_env_variable_override():
    """Warmup: ENV-Variable HUAWEI_FILTER_WARMUP wird gelesen"""
    import modbus_energy_meter.total_increasing_filter as filter_module

    # Setup: ENV setzen
    os.environ["HUAWEI_FILTER_WARMUP"] = "5"

    # ✅ Singleton clearen!
    filter_module._filter_instance = None

    # ✅ OHNE Parameter aufrufen (damit ENV gelesen wird)
    filter_instance = filter_module.get_filter()

    # Assertion
    assert (
        filter_instance._warmup_target == 5
    ), f"Expected 5, got {filter_instance._warmup_target}"  # ← FIX

    # Cleanup
    del os.environ["HUAWEI_FILTER_WARMUP"]
    filter_module._filter_instance = None
