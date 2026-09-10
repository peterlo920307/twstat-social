"""Parsing of East Asian era-based dates found in historical statistical tables.

Tables printed in Taiwan between 1895 and 1945 label their rows with a mixture of
Japanese and Republican era years. The typography is inconsistent: numerals are
often separated by spaces for justification, the Gregorian equivalent may or may
not be appended in parentheses, and the same table may mix four different period
conventions whose meanings do not coincide.

The period distinction matters. A "fiscal year end" figure is dated 31 March of
the following Gregorian year, while a "year end" figure is dated 31 December of
the same year. Merging the two produces a series that looks continuous and is
wrong by up to a year in places.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

__all__ = ["EraDate", "Period", "is_note", "parse"]


class Period(str, Enum):
    """The reporting convention a figure is dated by.

    Definitions follow the compilation notes of the 1946 Taiwanese compendium,
    clause 12: a fiscal year runs 1 April to 31 March; ``FISCAL_YEAR_END`` refers
    to 31 March of the following year; ``YEAR_END`` refers to 31 December.
    """

    CALENDAR_YEAR = "calendar_year"
    YEAR_END = "year_end"
    FISCAL_YEAR = "fiscal_year"
    FISCAL_YEAR_END = "fiscal_year_end"
    ACADEMIC_YEAR = "academic_year"


@dataclass(frozen=True)
class EraDate:
    """A parsed row label.

    ``year`` is the Gregorian year, or ``None`` when the label carries no year
    that can be resolved. ``raw`` preserves the original string so that a reader
    can always see what was interpreted.
    """

    year: int | None
    period: Period | None
    raw: str

    def __bool__(self) -> bool:
        """Truthy when a Gregorian year was resolved."""
        return self.year is not None


_GREGORIAN = re.compile(r"[(（]\s*(1[89]\d{2})\s*[)）]")
_NOTE = re.compile(r"^\s*(附\s*註|註|材料\s*來源|資料\s*來源|說\s*明|備\s*註|按)\s*[:：(（]?")

# Ordered longest-first: 年度底 must be tested before 年度 and 年.
_PERIODS: tuple[tuple[re.Pattern[str], Period], ...] = (
    (re.compile(r"學\s*年"), Period.ACADEMIC_YEAR),
    (re.compile(r"年\s*度\s*底"), Period.FISCAL_YEAR_END),
    (re.compile(r"年\s*度"), Period.FISCAL_YEAR),
    (re.compile(r"年\s*底"), Period.YEAR_END),
    (re.compile(r"年"), Period.CALENDAR_YEAR),
)


def is_note(text: object) -> bool:
    """Return ``True`` if ``text`` opens a footnote or a source attribution."""
    if text is None:
        return False
    return bool(_NOTE.match(str(text).strip()))


def parse(text: object) -> EraDate:
    """Interpret a row label.

    The Gregorian year is taken from the parenthesised form when present. Era
    numerals are not converted arithmetically: in this corpus the parenthesised
    year is authoritative and present on 91% of labels, and inferring the
    remainder from era numerals alone would introduce errors that no downstream
    check could detect.

    >>> parsed = parse("民國前 十 三 年度底(1899)")
    >>> parsed.year, parsed.period.value
    (1899, 'fiscal_year_end')
    >>> parse("附註:(1)國立臺灣大學直隸中央").year is None
    True
    """
    if text is None:
        return EraDate(None, None, "")
    raw = str(text).strip()
    if not raw or raw.lower() == "nan":
        return EraDate(None, None, raw)
    if _NOTE.match(raw):
        return EraDate(None, None, raw)

    match = _GREGORIAN.search(raw)
    year = int(match.group(1)) if match else None

    period = None
    for pattern, candidate in _PERIODS:
        if pattern.search(raw):
            period = candidate
            break

    return EraDate(year, period, raw)
