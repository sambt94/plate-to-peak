# ABOUTME: Makes the plugin's lib/ importable in tests without packaging.
# ABOUTME: Tests import parse_clarity / attribute / chart_data directly.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "plugins" / "plate-to-peak" / "lib"))
