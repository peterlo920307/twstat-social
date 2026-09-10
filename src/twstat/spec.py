"""Column specifications: which columns of a section mean what.

Header reconstruction is not automated. An attempt was made and it failed in a
way worth recording: because label characters are distributed across the columns
they span, a plausible-looking reconstruction can fuse two labels into one, or
absorb the table title into a column name, and produce output that passes any
obvious sanity check while being wrong.

Specifications are therefore written by hand, one per section, and every column
carries the note that it is machine-proposed until a human has checked it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["ColumnSpec", "SectionSpec", "SpecBook"]


@dataclass(frozen=True)
class ColumnSpec:
    """One spreadsheet column and the two dimensions it belongs to."""

    column: int
    """One-based column number, matching the spreadsheet."""

    dim1: str
    dim2: str | None = None
    """``None`` means the innermost header should supply this; an empty string
    means the column deliberately has no second dimension."""


@dataclass
class SectionSpec:
    """All columns of one section of one file."""

    file: str
    section: int
    columns: dict[int, ColumnSpec] = field(default_factory=dict)

    def add_range(self, start: int, end: int, dim1: str) -> None:
        """Assign ``dim1`` to every column from ``start`` to ``end`` inclusive."""
        for column in range(start, end + 1):
            existing = self.columns.get(column)
            self.columns[column] = ColumnSpec(column, dim1, existing.dim2 if existing else None)

    def set_dim2(self, column: int, dim2: str) -> None:
        existing = self.columns.get(column)
        self.columns[column] = ColumnSpec(column, existing.dim1 if existing else "", dim2)


class SpecBook:
    """Specifications for a whole corpus, keyed by file and section."""

    def __init__(self) -> None:
        self._sections: dict[tuple[str, int], SectionSpec] = {}

    def section(self, file: str, number: int) -> SectionSpec:
        key = (file, number)
        if key not in self._sections:
            self._sections[key] = SectionSpec(file, number)
        return self._sections[key]

    def define(
        self,
        file: str,
        sections: int | list[int],
        ranges: list[tuple[int, int, str]],
        dim2: dict[int, str] | None = None,
    ) -> None:
        """Define one layout, optionally shared by several sections of a file."""
        numbers = [sections] if isinstance(sections, int) else sections
        for number in numbers:
            spec = self.section(file, number)
            for start, end, dim1 in ranges:
                spec.add_range(start, end, dim1)
            for column, label in (dim2 or {}).items():
                spec.set_dim2(column, label)

    def get(self, file: str, section: int) -> SectionSpec | None:
        return self._sections.get((file, section))

    def files(self) -> set[str]:
        return {file for file, _ in self._sections}

    def __len__(self) -> int:
        return len(self._sections)
