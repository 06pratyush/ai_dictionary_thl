#!/usr/bin/env python3
"""Copy the corpora into the package so the wheel is self-contained.

data/*.json is the source of truth for the website. The package needs its own
copy inside the wheel -- a pip install has no repository around it -- and that
copy must never be edited by hand. This runs from build/build.py, so the two
cannot drift.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data"
DEST = ROOT / "thehallucinatedlab_dictionary" / "data"
FILES = ("ai-mathematics.json", "software-engineering.json")


def sync() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(SOURCE / name, DEST / name)
    return len(FILES)


if __name__ == "__main__":
    print(f"synced {sync()} corpus files into the package")
