"""The documentation index has to keep up with the documentation."""

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
INDEX = DOCS / "README.md"


def linked() -> set[str]:
    text = INDEX.read_text(encoding="utf-8")
    return set(re.findall(r"\]\((?!\.\./)([A-Za-z0-9_]+\.md)\)", text))


def test_every_document_is_in_the_index():
    present = {path.name for path in DOCS.glob("*.md")} - {"README.md"}
    assert present - linked() == set()


def test_the_index_has_no_broken_links():
    present = {path.name for path in DOCS.glob("*.md")}
    assert linked() - present == set()
