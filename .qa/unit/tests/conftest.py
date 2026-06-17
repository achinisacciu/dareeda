import sys
from pathlib import Path

ROOT = Path(__file__).resolve()
while ROOT.parent != ROOT and not (ROOT / "pyproject.toml").exists():
    ROOT = ROOT.parent

for p in (str(ROOT / "backend"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
