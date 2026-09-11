"""The release notes script, which the tag-triggered workflow depends on."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "changelog_entry.py"
spec = importlib.util.spec_from_file_location("changelog_entry", SCRIPT)
changelog_entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changelog_entry)

TEXT = """# Changelog

## 0.2.0 — 2027-01-01

Second.

### Fixed
- One thing.

## 0.1.0 — 2026-09-30

First.
"""


def test_an_entry_runs_to_the_next_version_heading():
    assert changelog_entry.entry("0.2.0", TEXT) == "Second.\n\n### Fixed\n- One thing.\n"


def test_the_last_entry_runs_to_the_end():
    assert changelog_entry.entry("0.1.0", TEXT) == "First.\n"


def test_a_version_that_is_not_there_stops_the_release():
    with pytest.raises(SystemExit):
        changelog_entry.entry("0.3.0", TEXT)


def test_a_version_is_not_matched_by_its_prefix():
    # 0.1 must not pick up the 0.1.0 entry.
    with pytest.raises(SystemExit):
        changelog_entry.entry("0.1", TEXT)


def test_the_current_version_has_an_entry():
    import twstat

    text = (SCRIPT.parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog_entry.entry(twstat.__version__, text).strip()
