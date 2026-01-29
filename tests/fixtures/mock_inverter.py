"""Mock für AsyncHuaweiSolar mit Test-Szenarien"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class MockRegisterValue:
    """Simuliert RegisterValue-Objekt von huawei-solar"""

    def __init__(self, value, unit=""):
        self.value = value
        self.unit = unit


class ModbusException(Exception):
    """Mock für Modbus-Exception"""

    pass


class MockHuaweiSolar:
    """Mock für AsyncHuaweiSolar mit konfigurierbaren Szenarien"""

    def __init__(self, scenario_file: Optional[str] = None):
        if scenario_file is None:
            scenario_file = str(Path(__file__).parent / "scenarios.yaml")

        self.scenario_file = scenario_file
        self.cycle = 0
        self.scenarios = self._load_scenarios()
        self.current_scenario = None

    def _load_scenarios(self) -> Dict:
        """Lädt Test-Szenarien aus YAML"""
        with open(self.scenario_file) as f:
            return yaml.safe_load(f)

    def load_scenario(self, name: str):
        """Aktiviert ein Test-Szenario"""
        if name not in self.scenarios:
            raise ValueError(
                f"Scenario '{name}' not found. Available: {list(self.scenarios.keys())}"
            )

        self.current_scenario = self.scenarios[name]
        self.cycle = 0

    async def get(self, register_name: str):
        """Simuliert Modbus-Read mit konfigurierten Werten/Fehlern"""
        if not self.current_scenario:
            raise ValueError("No scenario loaded! Call load_scenario() first")

        cycles = self.current_scenario["cycles"]
        cycle_data = cycles[min(self.cycle, len(cycles) - 1)]

        # Simuliere Modbus-Fehler
        if register_name in cycle_data.get("errors", []):
            raise ModbusException(f"Simulated error for {register_name}")

        # Gebe konfigurierten Wert zurück
        value = cycle_data.get(register_name, 0)
        return MockRegisterValue(value)

    def next_cycle(self):
        """Nächster Cycle für Tests"""
        self.cycle += 1
