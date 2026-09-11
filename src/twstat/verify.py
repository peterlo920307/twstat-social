"""Checking extracted numbers back against the cells they came from.

Every observation records the row and column it was read from, so the whole
dataset can be re-read from the source rather than sampled. That makes the check
complete rather than an accuracy estimate.

It checks numbers only. The meaning attached to a column is a separate question
that this cannot answer, and the errors it cannot see are the more serious ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .values import Flag
from .values import parse as parse_value

__all__ = ["Mismatch", "SourceNotFoundError", "verify"]


@dataclass(frozen=True)
class Mismatch:
    """One value that does not agree with the cell it was read from."""

    table_id: str
    src_row: int
    src_col: int
    reason: str


class SourceNotFoundError(LookupError):
    """Raised when a table in the data has no corresponding source file.

    Silently skipping such a table would let ``verify`` return an empty list for
    input it never actually checked, which is the one failure mode a verifier
    must not have.
    """


def verify(tidy: pd.DataFrame, raw_dir: str | Path) -> list[Mismatch]:
    """Re-read every row from its source cell and report disagreements.

    The source cell is parsed with the same rules the extraction used. Comparing
    against a bare ``float()`` instead would report the bracket artifacts as data
    errors, which is a mistake this function made until it was found.

    Every row is checked, including the ones with no value. Until
    ``docs/WORK.md`` R02 the 8,005 missing rows were skipped, so their
    coordinates were never read: every one could be set to row 9999 and this
    still reported no mismatches. A missing row now has to point at a cell that
    really holds no number.
    """
    raw_dir = Path(raw_dir)
    mismatches: list[Mismatch] = []

    for key, group in tidy.groupby("table_id"):
        table_id = str(key)
        candidates = sorted(raw_dir.glob(f"*{table_id}.xls")) + sorted(
            raw_dir.glob(f"*{table_id}.xlsx")
        )
        if not candidates:
            raise SourceNotFoundError(f"no source file for {table_id} under {raw_dir}")
        # Cell by cell from an object array. ``iterrows`` builds a Series per row
        # and ``DataFrame.iat`` boxes another per cell, which made this the
        # slowest command in the package by a factor of five.
        grid = pd.read_excel(candidates[0], header=None).to_numpy(dtype=object)
        for value, flag, src_row, src_col in zip(
            group["value"], group["flag"], group["src_row"], group["src_col"], strict=True
        ):
            row, column = int(src_row), int(src_col)

            def report(
                reason: str, table_id: str = table_id, row: int = row, column: int = column
            ) -> None:
                mismatches.append(Mismatch(table_id, row, column, reason))

            # A zero or negative coordinate would index from the far end of the
            # sheet without raising, so it has to be refused before the read.
            if row < 1 or column < 1:
                report("coordinate is not 1-based")
                continue
            try:
                cell = grid[row - 1, column - 1]
            except IndexError:
                report("out of range")
                continue

            parsed = parse_value(cell)
            if pd.isna(value):
                if parsed.number is not None:
                    report(f"recorded absent but source reads {parsed.number}")
                elif flag == Flag.MISSING.value and parsed.raw in ("", "nan"):
                    report("recorded as the missing mark but the source cell is empty")
                elif flag == Flag.MISSING.value and parsed.flag is not Flag.MISSING:
                    report(f"recorded missing but source reads {cell!r}")
                elif flag in (Flag.BLANK.value, Flag.COVERED.value) and parsed.raw not in (
                    "",
                    "nan",
                ):
                    report(f"recorded as empty but source reads {cell!r}")
                continue
            if parsed.number is None:
                report(f"unparsable: {cell!r}")
            elif abs(parsed.number - float(value)) > 1e-9:
                report(f"{parsed.number} != {value}")
            elif flag == Flag.BRACKET_ARTIFACT.value and parsed.flag is not Flag.BRACKET_ARTIFACT:
                report(f"recorded as braced but source reads {cell!r}")
    return mismatches
