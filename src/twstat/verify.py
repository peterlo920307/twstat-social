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
    """Re-read every value from its source cell and report disagreements.

    The source cell is parsed with the same rules the extraction used. Comparing
    against a bare ``float()`` instead would report the bracket artifacts as data
    errors, which is a mistake this function made until it was found.
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
        frame = pd.read_excel(candidates[0], header=None)
        for _, row in group.iterrows():
            if pd.isna(row["value"]):
                continue
            try:
                cell = frame.iat[int(row["src_row"]) - 1, int(row["src_col"]) - 1]
            except IndexError:
                mismatches.append(
                    Mismatch(table_id, row["src_row"], row["src_col"], "out of range")
                )
                continue
            expected = parse_value(cell).number
            if expected is None:
                mismatches.append(
                    Mismatch(table_id, row["src_row"], row["src_col"], f"unparsable: {cell!r}")
                )
            elif abs(expected - float(row["value"])) > 1e-9:
                mismatches.append(
                    Mismatch(
                        table_id,
                        row["src_row"],
                        row["src_col"],
                        f"{expected} != {row['value']}",
                    )
                )
    return mismatches
