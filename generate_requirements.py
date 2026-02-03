"""
Generate requirements.txt from pyproject.toml for Docker builds.
"""

import tomllib
from pathlib import Path


def generate_requirements():
    # Read pyproject.toml
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    # Extract dependencies
    deps = data["project"]["dependencies"]

    # Write to addon folder
    addon_path = Path("huawei_solar_modbus_mqtt/requirements.txt")
    with open(addon_path, "w") as f:
        f.write("\n".join(deps) + "\n")

    print(f"✅ Generated {addon_path} with {len(deps)} dependencies")


if __name__ == "__main__":
    generate_requirements()
