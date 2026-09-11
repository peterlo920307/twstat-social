"""Print one version's entry from CHANGELOG.md, for use as release notes.

python scripts/changelog_entry.py 0.1.0
"""

import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"


def entry(version: str, text: str) -> str:
    """Return the body under ``## <version>``, up to the next version heading."""
    # Followed by a space or the end of the line, not merely a word boundary:
    # "." counts as a boundary, so 0.1 would otherwise find the 0.1.0 entry.
    heading = re.compile(rf"^## {re.escape(version)}(?=\s|$).*$", re.MULTILINE)
    found = heading.search(text)
    if found is None:
        raise SystemExit(f"CHANGELOG.md has no entry for {version}")
    following = re.compile(r"^## ", re.MULTILINE).search(text, found.end())
    body = text[found.end() : following.start() if following else len(text)]
    return body.strip() + "\n"


def main() -> int:
    """Print the entry named on the command line."""
    if len(sys.argv) != 2:
        raise SystemExit("usage: changelog_entry.py VERSION")
    sys.stdout.write(entry(sys.argv[1], CHANGELOG.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
