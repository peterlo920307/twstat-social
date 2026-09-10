"""Conversion of a specified spreadsheet into tidy rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from . import sections as sectioning
from .eradate import parse as parse_date
from .spec import SpecBook
from .values import Flag
from .values import parse as parse_value

__all__ = ["Observation", "extract_file", "extract_corpus", "COLUMNS"]

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
                column + 1: sectioning.clean(frame.iat[headers[-1], column])
                for column in range(frame.shape[1])
            }
            if headers
            else {}
        )
        label = (section.label or "").lstrip("0123456789.")
        for row in range(first, section.end):
            date = parse_date(frame.iat[row, 0])
            if date.year is None:
                continue
            for column, column_spec in section_spec.columns.items():
                index = column - 1
                if index >= frame.shape[1]:
                    continue
                value = parse_value(frame.iat[row, index])
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
                        dim2=_dim2(column_spec, bottom, column),
                        value=value.number,
                        flag=value.flag.value if value.flag else None,
                        src_row=row + 1,
                        src_col=column,
                    )
                )
    return pd.DataFrame([asdict(row) for row in rows], columns=COLUMNS)


def extract_corpus(raw_dir: str | Path, spec: SpecBook) -> pd.DataFrame:
    """Extract every file for which a specification exists."""
    raw_dir = Path(raw_dir)
    frames = [
        extract_file(path, spec)
        for path in sorted(raw_dir.glob("*.xls"))
        if path.stem in spec.files()
    ]
    frames = [frame for frame in frames if len(frame)]
    if not frames:
        return pd.DataFrame(columns=COLUMNS)
    return pd.concat(frames, ignore_index=True)
