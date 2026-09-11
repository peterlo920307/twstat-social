"""Recovery of the compilers' own footnotes and source attributions.

Clause 9 of the compilation notes says that figures which could not be corrected
were annotated in the footnote column. Those footnotes are therefore the
compilers' own record of data quality, and they carry information the numbers do
not: institutional histories that explain discontinuities, the specific
publication each table was drawn from, and statements of what was excluded.

One of them settles a question the numbers cannot: table 481 notes that
indigenous children were not counted in the school-age population before 1921.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import sections as sectioning

__all__ = ["ITEM_COLUMNS", "Note", "extract_notes", "note_items"]

_HEAD = re.compile(r"^\s*(附\s*註|註|材料\s*來源|資料\s*來源|說\s*明|備\s*註|按)\s*[:：(（]?")
_SOURCE = re.compile(r"^\s*(材料\s*來源|資料\s*來源)")
_YEAR = re.compile(r"\(1[89]\d{2}\)")


@dataclass(frozen=True)
class Note:
    """One footnote or source attribution, with where it was found."""

    file: str
    table_id: str
    section: int
    section_label: str
    src_row: int
    kind: str
    text: str


def _kind(text: str) -> str:
    return "source" if _SOURCE.match(text) else "note"


def extract_notes(path: str | Path) -> list[Note]:
    """Read the footnotes of one file, joining lines that continue a note."""
    path = Path(path)
    stem = path.stem
    frame = pd.read_excel(path, header=None)
    # Read cells from an object array; DataFrame.iat builds a pandas object each time.
    grid = frame.to_numpy(dtype=object)
    sections = sectioning.find(frame)

    def locate(row: int) -> tuple[int, str]:
        for section in sections:
            if section.start <= row < section.end:
                return section.number, sectioning.label_text(section)
        return 1, ""

    notes: list[Note] = []
    row = 0
    while row < len(frame):
        head = None
        for column in range(min(4, frame.shape[1])):
            text = sectioning.clean(grid[row, column])
            if text and _HEAD.match(text):
                head = text
                break
        if head is None:
            row += 1
            continue

        parts, cursor = [head], row + 1
        while cursor < len(frame):
            following = sectioning.clean(grid[cursor, 0])
            if not following or _HEAD.match(following) or _YEAR.search(following):
                break
            # A note printed at the foot of one part runs straight into the
            # heading of the next when no blank row separates them, and the
            # heading is long enough to pass for a continuation line.
            if sectioning.is_marker(following):
                break
            if len(following) < 4:
                break
            parts.append(following)
            cursor += 1

        number, label = locate(row)
        notes.append(
            Note(
                file=stem,
                table_id=stem.split("_")[-1],
                section=number,
                section_label=label,
                src_row=row + 1,
                kind=_kind(head),
                text="".join(parts),
            )
        )
        row = cursor
    return notes


# A numbered item inside a note: "(1)", "（2）". One or two digits only, so a
# Gregorian year in brackets, "(1931)", is not read as a marker.
_ITEM = re.compile(r"[(（](\d{1,2})[)）]")
ITEM_COLUMNS = ["table_id", "section_label", "marker", "text", "src_row"]


def note_items(notes: pd.DataFrame) -> pd.DataFrame:
    """Split each footnote into its numbered items, one row per item.

    A label in the tidy data such as ``閱覽人數(1)`` points at item 1 of a note
    to the same table, and this is the table that pointer resolves against. Join
    on ``table_id``, ``section_label`` and ``marker``.

    ``section_label`` rather than the section number, because notes follow the
    printed page and not the table's structure. Mt487-2 prints its only note at
    the foot of the first of five header bands, and the note applies to all five;
    the bands share a heading, so they share its notes.
    """
    rows: list[dict[str, object]] = []
    for table_id, label, kind, text, src_row in zip(
        notes["table_id"],
        notes["section_label"],
        notes["kind"],
        notes["text"],
        notes["src_row"],
        strict=True,
    ):
        if kind != "note":
            continue
        marks = list(_ITEM.finditer(text))
        for index, mark in enumerate(marks):
            end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
            rows.append(
                {
                    "table_id": table_id,
                    "section_label": label if isinstance(label, str) else "",
                    "marker": int(mark.group(1)),
                    "text": text[mark.end() : end].strip(),
                    "src_row": src_row,
                }
            )
    return pd.DataFrame(rows, columns=ITEM_COLUMNS)
