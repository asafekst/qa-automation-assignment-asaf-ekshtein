#!/usr/bin/env python3
"""Fail CI/local if forbidden flakiness patterns appear in test code."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = (ROOT / "tests", ROOT / "pages")
SCAN_FILES = (ROOT / "conftest.py", ROOT / "constants.py")

# Playwright auto-wait + expect() only — no time-based or implicit-style waits.
FORBIDDEN = (
    (re.compile(r"\btime\.sleep\s*\("), "time.sleep()"),
    (re.compile(r"\bThread\.sleep\s*\("), "Thread.sleep()"),
    (re.compile(r"\.wait_for_timeout\s*\("), "page.wait_for_timeout()"),
    (re.compile(r"wait_for_load_state\s*\(\s*['\"]networkidle['\"]"), "networkidle load state"),
    (
        re.compile(r"^[ \t]+(import |from .+ import )", re.MULTILINE),
        "inline import (move to top of file)",
    ),
)


def _paths() -> list[Path]:
    paths: list[Path] = [p for p in SCAN_FILES if p.is_file()]
    for folder in SCAN_DIRS:
        if folder.is_dir():
            paths.extend(folder.rglob("*.py"))
    return paths


def main() -> int:
    violations: list[str] = []
    for path in _paths():
        text = path.read_text(encoding="utf-8")
        for pattern, label in FORBIDDEN:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(f"{path.relative_to(ROOT)}:{line}: {label}")

    if violations:
        print("Anti-flakiness check failed:\n" + "\n".join(violations))
        return 1

    print("Anti-flakiness check passed (no sleep / wait_for_timeout / networkidle).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
