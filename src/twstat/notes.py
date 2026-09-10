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

__all__ = ["Note", "extract_notes"]

_HEAD = re.compile(r"^\s*(附\s*註|註|材料\s*來源|資料\s*來源|說\s*明|備\s*註|按)\s*[:：(（]?")
_SOURCE = re.compile(r"^\s*(材料\s*來源|資料\s*來源)")
_YEAR = re.compile(r"\(1[89]\d{2}\)")


@dataclass(frozen=True)
class Note:
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
    sections = sectioning.find(frame)

    def locate(row: int) -> tuple[int, str]:
        for section in sections:
            if section.start <= row < section.end:
                return section.number, (section.label or "")
        return 1, ""

    notes: list[Note] = []
    row = 0
    while row < len(frame):
        head = None
        for column in range(min(4, frame.shape[1])):
            text = sectioning.clean(frame.iat[row, column])
            if text and _HEAD.match(text):
                head = text
                break
        if head is None:
            row += 1
            continue

        parts, cursor = [head], row + 1
        while cursor < len(frame):
            following = sectioning.clean(frame.iat[cursor, 0])
            if not following or _HEAD.match(following) or _YEAR.search(following):
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
                section_label=label.lstrip("0123456789."),
                src_row=row + 1,
                kind=_kind(head),
                text="".join(parts),
            )
        )
        row = cursor
    return notes
