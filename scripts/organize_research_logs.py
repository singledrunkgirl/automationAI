#!/usr/bin/env python3
"""Move technical execution logs from Projects/research/ to data/archive/ for long-term storage."""
import shutil
from pathlib import Path
import sys

SOURCE = Path("/home/kali/HackWithAI/Projects/research")
DEST = Path("/home/kali/HackWithAI/data/archive")
LOG_PATTERNS = ["*.json", "*.log", "*.txt"]

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    moved = 0
    for pattern in LOG_PATTERNS:
        for f in SOURCE.glob(pattern):
            if f.name.startswith("overflow_test_") or f.name.endswith("_config.json") or f.name.endswith("_rules.json"):
                try:
                    shutil.move(str(f), str(DEST / f.name))
                    print(f"Moved: {f.name}")
                    moved += 1
                except Exception as e:
                    print(f"Error moving {f.name}: {e}")
    print(f"Total files moved: {moved}")

if __name__ == "__main__":
    main()
