"""The documentation index has to keep up with the documentation."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
INDEX = DOCS / "README.md"

# The target of an inline Markdown link, up to a space (an optional title) or
# the closing bracket.
LINK = re.compile(r"\]\(([^)\s]+)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def linked() -> set[str]:
    text = INDEX.read_text(encoding="utf-8")
    return set(re.findall(r"\]\((?!\.\./)([A-Za-z0-9_]+\.md)\)", text))


def relative_links() -> list[tuple[Path, str]]:
    pages = sorted([*ROOT.glob("*.md"), *DOCS.glob("*.md")])
    return [
        (page, target)
        for page in pages
        for target in LINK.findall(page.read_text(encoding="utf-8"))
        if not SCHEME.match(target) and not target.startswith("#")
    ]


def test_every_document_is_in_the_index():
    present = {path.name for path in DOCS.glob("*.md")} - {"README.md"}
    assert present - linked() == set()


def test_every_relative_link_resolves():
    # Every page in the repository root and in docs/, and every kind of
    # relative link: docs/X.md from the root, ../README.md from docs/, and
    # links to data files. The index check above sees only flat links in one
    # file.
    links = relative_links()
    assert (ROOT / "README.md", "docs/README.md") in links
    assert (DOCS / "EXAMPLE.md", "../README.md") in links
    broken = [
        f"{page.relative_to(ROOT).as_posix()}: {target}"
        for page, target in links
        if not (page.parent / target.split("#")[0]).exists()
    ]
    assert broken == []
