"""Detection of several tables stacked inside one spreadsheet file.

The compilers state in clause 7 of their notes that where a statistical category
changed too much to be merged across years, they "cut it into several parts and
listed them separately". In the digitised files those parts appear one below
another in a single sheet, each with its own header rows and sometimes a
different column layout.

Eleven of the fifty files in the source corpus are affected. Reading such a file
as one table silently merges unrelated populations: in two education tables it
merges Taiwanese and Japanese pupils into a single series, which no value-level
check can detect because every individual number is correct.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from .eradate import parse as parse_date

__all__ = ["Section", "clean", "find", "header_rows"]

_MARKER = re.compile(r"^\d+\.[^\d]")


def clean(cell: object) -> str | None:
    """Strip a cell to comparable text, or ``None`` if it is empty."""
    if cell is None or str(cell) == "nan":
        return None
    text = re.sub(r"\s+", "", str(cell)).strip()
    return text or None


@dataclass(frozen=True)
class Section:
    """One table within a sheet that may hold several."""

    number: int
    label: str | None
    start: int
    end: int
    """Row range, zero-based and half-open."""


def find(frame: pd.DataFrame, scan_columns: int = 5) -> list[Section]:
    """Split a sheet at its section markers.

    Markers are numbered headings such as ``1.臺中農林專門學校``, placed in one of
    the leftmost columns. A sheet with no markers is returned as a single
    section covering the whole frame.
    """
    marks: list[tuple[int, str]] = []
    for row in range(len(frame)):
        for column in range(min(scan_columns, frame.shape[1])):
            text = clean(frame.iat[row, column])
            if text and _MARKER.match(text) and len(text) < 40:
                marks.append((row, text))
                break
    if not marks:
        return [Section(1, None, 0, len(frame))]

    sections = []
    for index, (row, label) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(frame)
        sections.append(Section(index + 1, label, row, end))
    return sections


def header_rows(frame: pd.DataFrame, section: Section) -> tuple[int | None, list[int]]:
    """Locate the first data row of a section and the header rows above it.

    Returns ``(None, [])`` for a section with no dated rows, which in this corpus
    means a cross-sectional snapshot rather than a time series.
    """
    first = None
    for row in range(section.start, section.end):
        if parse_date(frame.iat[row, 0]).year is not None:
            first = row
            break
    if first is None:
        return None, []

    headers = [
        row
        for row in range(section.start, first)
        if any(clean(frame.iat[row, column]) for column in range(1, frame.shape[1]))
    ]
    headers = [
        row
        for row in headers
        if not (clean(frame.iat[row, 0]) or "").startswith("表")
        and not _MARKER.match(clean(frame.iat[row, 0]) or "")
    ]
    return first, headers
