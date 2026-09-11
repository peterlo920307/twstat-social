"""Conversion of a specified spreadsheet into tidy rows.

The specification says which columns mean what. The innermost header row is read
from the sheet rather than restated, because it is usually right and always
closer to the printed page than a hand-typed copy. Everything else about a row —
its year, its reporting convention, whether its label carries a second dimension
— is read from the row itself, and a row that looks dated but cannot be read is
refused rather than skipped.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import pandas as pd

from . import sections as sectioning
from .eradate import parse as parse_date
from .spec import SpecBook
from .values import Flag, Value
from .values import parse as parse_value

# A row label carrying a bracketed number and a period word is meant to be a
# dated row. If no year can be read from it, the source has a misprint and the
# row must not be skipped in silence: Welfare_Mt504 lost its 1903 row that way,
# printed as (1093). Correct it with SpecBook.correct_year, or fix the parser.
_LOOKS_DATED = re.compile(r"[(（]\s*\d{3,5}\s*[)）]")

# A year split across two rows by a brace drawn in the label column:
#     民國  二  十年(1931)┌患者
#                        └死亡
# Only the first row carries the year. The second used to be skipped because it
# had none, which discarded about 1,900 figures from Mt487-2 and Mt489 and left
# the survivors as case counts with nothing in the schema saying so. The word
# after the brace is a second dimension of the row, and goes into dim2.
_STUB = re.compile(r"([┌├└])\s*(\S+)\s*$")

# Unassigned private-use characters left by the 2006 digitisation. They render
# as a missing glyph and carry nothing.
_PRIVATE_USE = re.compile(r"[\ue000-\uf8ff]")

__all__ = ["COLUMNS", "Observation", "extract_corpus", "extract_file"]

COLUMNS = [
    "table_id",
    "section",
    "section_label",
    "year",
    "period_type",
    "dim1",
    "dim2",
    "value",
    "flag",
    "src_row",
    "src_col",
]


@dataclass(frozen=True)
class Observation:
    """One number, with everything needed to find it again in the source."""

    table_id: str
    section: int
    section_label: str
    year: int
    period_type: str | None
    dim1: str
    dim2: str | None
    value: float | None
    flag: str | None
    src_row: int
    src_col: int


def _join(column: str | None, row: str | None) -> str | None:
    """Combine a column's second dimension with one read from the row label."""
    if column and row:
        return f"{column}·{row}"
    return column or row


def _dim2(column_spec, bottom: dict[int, str | None], column: int) -> str | None:
    """Resolve the second dimension, preferring an explicit specification."""
    if column_spec.dim2 is not None:
        return column_spec.dim2 or None
    return bottom.get(column) or None


def extract_file(path: str | Path, spec: SpecBook, table_id: str | None = None) -> pd.DataFrame:
    """Extract every specified column of every section of one file."""
    path = Path(path)
    stem = path.stem
    table_id = table_id or stem.split("_")[-1]
    frame = pd.read_excel(path, header=None)
    grid = frame.to_numpy(dtype=object)

    rows: list[Observation] = []
    for section in sectioning.find(frame):
        section_spec = spec.get(stem, section.number)
        if section_spec is None:
            continue
        first, headers = sectioning.header_rows(frame, section)
        if first is None:
            continue
        # The lowest header row usually names the innermost dimension. It is read
        # from the sheet rather than restated in the specification, which only
        # carries overrides for the cases where that row is itself fragmented.
        bottom = (
            {
                column + 1: sectioning.clean(grid[headers[-1], column])
                for column in range(frame.shape[1])
            }
            if headers
            else {}
        )
        label = _PRIVATE_USE.sub("", section.label or "").lstrip("0123456789.．").strip()
        carried = None
        for row in range(first, section.end):
            text = grid[row, 0]
            date = parse_date(text)
            corrected = spec.corrected_year(stem, row + 1)
            if corrected is not None:
                date = replace(date, year=corrected)
            stub = _STUB.search(text) if isinstance(text, str) else None
            if date.year is not None:
                # A dated row opening a brace lends its date to the rows it joins.
                carried = date if stub and stub.group(1) == "┌" else None
            elif stub and stub.group(1) in "├└" and carried is not None:
                date = carried
                if stub.group(1) == "└":
                    carried = None
            else:
                carried = None
                if date.period is not None and _LOOKS_DATED.search(str(text)):
                    raise ValueError(
                        f"{stem} row {row + 1}: {str(text).strip()!r} looks dated but "
                        "gives no year; record the right one with SpecBook.correct_year"
                    )
                continue
            # carried is only ever taken from a row that had a year.
            assert date.year is not None
            row_dim = stub.group(2) if stub else None
            for column, column_spec in section_spec.columns.items():
                index = column - 1
                if index >= frame.shape[1]:
                    continue
                value = parse_value(grid[row, index])
                if value.flag is Flag.LESS_THAN_ONE_UNIT and section_spec.zero_is_exact:
                    value = Value(0.0, None, value.raw)
                if value.number is None and value.flag in (None, Flag.NON_NUMERIC):
                    # Stray text in a numeric column is not an observation.
                    continue
                rows.append(
                    Observation(
                        table_id=table_id,
                        section=section.number,
                        section_label=label,
                        year=date.year,
                        period_type=date.period.value if date.period else None,
                        dim1=column_spec.dim1,
                        dim2=_join(_dim2(column_spec, bottom, column), row_dim),
                        value=value.number,
                        flag=value.flag.value if value.flag else None,
                        src_row=row + 1,
                        src_col=column,
                    )
                )
    return pd.DataFrame([asdict(row) for row in rows], columns=COLUMNS)


SPREADSHEET_SUFFIXES = (".xls", ".xlsx")


def extract_corpus(raw_dir: str | Path, spec: SpecBook) -> pd.DataFrame:
    """Extract every file for which a specification exists.

    Both spreadsheet suffixes are accepted. The source corpus is ``.xls``, but
    restricting the search to that extension makes the function silently return
    nothing for a directory of ``.xlsx`` files.
    """
    raw_dir = Path(raw_dir)
    paths = sorted(path for suffix in SPREADSHEET_SUFFIXES for path in raw_dir.glob(f"*{suffix}"))
    frames = [extract_file(path, spec) for path in paths if path.stem in spec.files()]
    frames = [frame for frame in frames if len(frame)]
    if not frames:
        return pd.DataFrame(columns=COLUMNS)
    return pd.concat(frames, ignore_index=True)
