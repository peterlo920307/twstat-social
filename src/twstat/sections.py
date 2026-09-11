"""Detection of several tables stacked inside one spreadsheet file.

The compilers state in clause 7 of their notes that where a statistical category
changed too much to be merged across years, they "cut it into several parts and
listed them separately". In the digitised files those parts appear one below
another in a single sheet, each with its own header rows and sometimes a
different column layout.

Eleven of the fifty files in the source corpus are affected. Reading such a file
as one table silently merges unrelated populations: in two education tables it
merged Taiwanese and Japanese pupils into a single series, which no value-level
check can detect because every individual number is correct.

Not every part is announced by a numbered marker. Three of the health tables run
five or six header bands down a single sheet, each re-using the same physical
columns for a different set of diseases and each carrying its own full run of
years. Nothing separates them but the header band itself. Splitting only on
markers published 2,976 rows under the first band's disease names; see
``docs/W06_layout.md``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .eradate import parse as parse_date
from .values import parse as parse_value

__all__ = ["Section", "clean", "find", "header_rows", "is_marker", "label_text"]

# A section marker is a number, a full stop and a label: "1.本省人". The stop is
# written both as an ASCII period and as the full-width U+FF0E, and the two are
# indistinguishable in print. Accepting only the ASCII form missed 117 markers
# across 102 of the 599 tables tested in docs/W06_layout.md, and in 6 of those
# files it merged two sections into one. None of them is in the three chapters
# this package was written against, which is why it survived as long as it did.
_MARKER = re.compile(r"^\d+[.．][^\d]")


# Unassigned private-use characters left by the 2006 digitisation. They render
# as a missing glyph and carry nothing.
_PRIVATE_USE = re.compile(r"[\ue000-\uf8ff]")


def is_marker(text: str | None) -> bool:
    """Return ``True`` if ``text`` opens a numbered section, as in ``1.本省人``.

    Callers outside this module used to reach for the pattern itself; this is
    the supported way to ask.
    """
    return bool(text) and bool(_MARKER.match(text or ""))


def label_text(section: Section) -> str:
    """Return a section's heading as it should appear in the published files.

    The marker number and its stop are dropped, in either the ASCII or the
    full-width form, and so is any private-use character. The tidy data and the
    notes must clean labels the same way, because a reader joins them on it.
    """
    return _PRIVATE_USE.sub("", section.label or "").lstrip("0123456789.．").strip()


def _grid(frame: pd.DataFrame) -> np.ndarray:
    """Return the sheet as a plain object array for cell-by-cell reading.

    ``DataFrame.iat`` builds a pandas object for every cell it returns, which
    costs about seventy times as much as indexing the array and was the largest
    single cost of an extraction.
    """
    return frame.to_numpy(dtype=object)


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


def _is_header_band(grid: np.ndarray, row: int) -> bool:
    """Return ``True`` if this row reads as column headings rather than data.

    Two or more cells right of the label column that hold text no number can be
    read out of. One such cell is a unit note or a stray mark; two is a heading.
    A cell that opens with a digit is a quantity with its unit, such as the
    conversion rates 「33.5公升」 printed across one forestry table, and not a
    heading, so it does not count.
    """
    found = 0
    for column in range(1, grid.shape[1]):
        text = clean(grid[row, column])
        if not text or text[0].isdigit():
            continue
        value = parse_value(text)
        if value.number is None and value.flag is not None and value.flag.value == "non_numeric":
            found += 1
            if found >= 2:
                return True
    return False


def _band_starts(grid: np.ndarray, start: int, end: int) -> list[int]:
    """Rows within ``start:end`` where a fresh header band begins after data.

    The band above the first data row is the section's own header and is not
    returned; only a band that interrupts the data is a new part.
    """
    starts: list[int] = []
    seen_data = False
    pending: int | None = None
    for row in range(start, end):
        if parse_date(grid[row, 0]).year is not None:
            if pending is not None and seen_data:
                starts.append(pending)
            pending, seen_data = None, True
            continue
        if pending is None and _is_header_band(grid, row):
            pending = row
    return starts


def find(frame: pd.DataFrame, scan_columns: int = 5) -> list[Section]:
    """Split a sheet into the tables it holds.

    Two things separate one table from the next. A numbered heading such as
    ``1.臺中農林專門學校`` in one of the leftmost columns, and a fresh band of
    column headings part-way down a table that otherwise looks continuous. The
    second kind is not announced at all, and missing it is the more dangerous of
    the two: the figures stay correct and only their labels are wrong.

    A sheet with neither is returned as a single section covering the frame.
    """
    grid = _grid(frame)
    marks: list[tuple[int, str | None]] = []
    for row in range(len(frame)):
        for column in range(min(scan_columns, grid.shape[1])):
            text = clean(grid[row, column])
            if text and _MARKER.match(text) and len(text) < 40:
                marks.append((row, text))
                break
    if not marks:
        marks = [(0, None)]

    bounds: list[tuple[int, str | None]] = []
    for index, (row, label) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(frame)
        bounds.append((row, label))
        # A continuation band keeps the heading it was printed under.
        bounds.extend((band, label) for band in _band_starts(grid, row, end))

    sections = []
    for index, (row, label) in enumerate(bounds):
        end = bounds[index + 1][0] if index + 1 < len(bounds) else len(frame)
        sections.append(Section(index + 1, label, row, end))
    return sections


def header_rows(frame: pd.DataFrame, section: Section) -> tuple[int | None, list[int]]:
    """Locate the first data row of a section and the header rows above it.

    Returns ``(None, [])`` for a section with no dated rows, which in this corpus
    means a cross-sectional snapshot rather than a time series.
    """
    grid = _grid(frame)
    first = None
    for row in range(section.start, section.end):
        if parse_date(grid[row, 0]).year is not None:
            first = row
            break
    if first is None:
        return None, []

    headers = [
        row
        for row in range(section.start, first)
        if any(clean(grid[row, column]) for column in range(1, grid.shape[1]))
    ]
    headers = [
        row
        for row in headers
        if not (clean(grid[row, 0]) or "").startswith("表")
        and not _MARKER.match(clean(grid[row, 0]) or "")
    ]
    return first, headers
