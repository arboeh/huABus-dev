# tests\conftest.py

"""Pytest Configuration"""

import sys
from pathlib import Path

# Füge den huawei-solar-modbus-mqtt Ordner hinzu
addon_path = Path(__file__).parent.parent / "huawei-solar-modbus-mqtt"
sys.path.insert(0, str(addon_path))

print(f"✅ conftest.py loaded! Added to sys.path: {addon_path}")
