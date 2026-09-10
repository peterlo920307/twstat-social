"""Interpretation of cell values, including the source's own missing-value legend.

Clause 11 of the 1946 compilation notes defines three markers: a dash for
"not surveyed or no figure", an ellipsis for "figure unknown", and a zero for
"a quantity of less than one unit". The zero is the dangerous one. It is not
zero, and treating it as such biases any mean computed over the column.

The 2006 digitisation collapsed the dash and the ellipsis into a single full
stop, so the distinction between "not surveyed" and "unknown" cannot be
recovered from the spreadsheets alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

__all__ = ["Flag", "Value", "parse"]


class Flag(str, Enum):
    """Why a value is absent, or why it needed interpretation."""

    MISSING = "missing"
    """Marked absent in the source. Must not be filled with zero."""

    LESS_THAN_ONE_UNIT = "less_than_one_unit"
    """Printed as ``0``, meaning a quantity below one unit. Left-censored."""

    BRACKET_ARTIFACT = "bracket_artifact"
    """Printed as ``└─N─┘``, a typesetting mark for a value spanning rows."""

    NON_NUMERIC = "non_numeric"
    """Text where a number was expected, usually a stray note."""


@dataclass(frozen=True)
class Value:
    """A cell, as a number where one could be read and a reason where none could."""

    number: float | None
    flag: Flag | None
    raw: str

    def __bool__(self) -> bool:
        """Truthy when a number was read."""
        return self.number is not None


_MISSING = {".", "．", "…", "‥", "-", "－", "―", "─", ""}
_BRACKET = re.compile(r"^└─\s*([\d,.]+)\s*─┘$")


def parse(cell: object) -> Value:
    """Interpret a single cell.

    >>> parse("69").number
    69.0
    >>> parse(".").flag
    <Flag.MISSING: 'missing'>
    >>> parse("0").flag
    <Flag.LESS_THAN_ONE_UNIT: 'less_than_one_unit'>
    >>> parse("└─42─┘").number
    42.0
    """
    if cell is None:
        return Value(None, Flag.MISSING, "")
    raw = str(cell).strip()
    if raw in _MISSING or raw.lower() == "nan":
        return Value(None, Flag.MISSING, raw)

    bracket = _BRACKET.match(raw)
    if bracket:
        try:
            return Value(float(bracket.group(1).replace(",", "")), Flag.BRACKET_ARTIFACT, raw)
        except ValueError:
            return Value(None, Flag.BRACKET_ARTIFACT, raw)

    try:
        number = float(raw.replace(",", "").replace(" ", ""))
    except ValueError:
        return Value(None, Flag.NON_NUMERIC, raw)

    if number == 0:
        return Value(0.0, Flag.LESS_THAN_ONE_UNIT, raw)
    return Value(number, None, raw)
