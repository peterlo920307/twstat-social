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
    """Marked absent in the source with the compilers' dot. Must not be filled
    with zero. The 2006 digitisation merged their 「－」 (not surveyed) and 「…」
    (unknown) into this one mark."""

    BLANK = "blank"
    """The cell is empty in the source: nothing was printed there at all, which
    is different evidence from a printed mark. Often a category that did not yet
    exist. Set by the extractor, which can see the row; ``parse`` alone cannot."""

    COVERED = "covered"
    """Empty because the braced figure to its left spans it. That figure is the
    combined total for its own column and every covered column that follows it
    in the row, so neither column can be read on its own. Set by the extractor."""

    LESS_THAN_ONE_UNIT = "less_than_one_unit"
    """Printed as ``0``, meaning a quantity below one unit. Left-censored."""

    BRACKET_ARTIFACT = "bracket_artifact"
    """Printed as ``└─N─┘``, a mark for a value spanning printed columns."""

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

# A figure that spans several printed columns is set inside a drawn brace, and
# the digitisation kept the brace in the cell. The brace is drawn with whatever
# combination of corner and rule characters made the width come out right, so
# the number can be wrapped as └─42─┘, ┌──126──┐, └───────76───────┘, or with a
# single corner on one side only. Matching one of those spellings and not the
# others discards figures: the narrow pattern used until docs/W06_layout.md lost
# 102 values in the published corpus alone.
_BRACE = re.compile(r"^[┌└├┐┘┤│]?[─—]*\s*(.+?)\s*[─—]*[┌└├┐┘┤│]?$")
_BRACE_CHARS = "┌└├┐┘┤│─—"

# The compilers cross-reference their own footnotes by printing the marker in
# front of the figure: "(1)    10". The number is perfectly readable and the
# marker points at a note that data/notes.csv already carries. Rejecting the
# whole cell threw 23 figures out of the published corpus.
_FOOTNOTE_MARKER = re.compile(r"^[(（]\s*\d+\s*[)）]\s*")


def _number(text: str) -> float | None:
    """Read a decimal number, or return ``None`` if the text is not one.

    A leading footnote marker is stripped and thousands separators are dropped.
    Anything else, a date such as ``32.12.22`` included, is not a number:
    ``float`` would reject it and so does this.

    >>> _number("(1)    10")
    10.0
    >>> _number("32.12.22") is None
    True
    """
    text = _FOOTNOTE_MARKER.sub("", text)
    try:
        return float(text.replace(",", "").replace(" ", ""))
    except ValueError:
        return None


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
    >>> parse("┌────298────┐").number
    298.0
    >>> parse("└32.12.22").flag
    <Flag.NON_NUMERIC: 'non_numeric'>
    """
    if cell is None:
        return Value(None, Flag.MISSING, "")
    raw = str(cell).strip()
    if raw in _MISSING or raw.lower() == "nan":
        return Value(None, Flag.MISSING, raw)

    if any(character in raw for character in _BRACE_CHARS):
        brace = _BRACE.match(raw)
        inner = brace.group(1) if brace else ""
        # A brace can hold the compilers' missing marker as readily as a figure,
        # and when it does the cell means missing, not unreadable.
        if inner in _MISSING:
            return Value(None, Flag.MISSING, raw)
        number = _number(inner)
        if number is not None:
            return Value(number, Flag.BRACKET_ARTIFACT, raw)
        return Value(None, Flag.NON_NUMERIC, raw)

    number = _number(raw)
    if number is None:
        return Value(None, Flag.NON_NUMERIC, raw)

    if number == 0:
        return Value(0.0, Flag.LESS_THAN_ONE_UNIT, raw)
    return Value(number, None, raw)
