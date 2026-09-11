"""Column specifications, and the shape of the hand-written 1946 book.

The book is checked here without the source files so that a malformed entry is
caught in CI, where the corpus tests do not run. Its size is deliberately not
asserted: sections are added and split as layouts are re-read, and a count here
would only have to be edited each time.
"""

import re

import pytest

from twstat.corpus1946 import build
from twstat.spec import ColumnSpec, SectionSpec, SpecBook


@pytest.fixture(scope="module")
def book() -> SpecBook:
    return build()


def _sections(book: SpecBook) -> list[SectionSpec]:
    found = [
        spec
        for file in sorted(book.files())
        for number in range(1, 100)
        if (spec := book.get(file, number)) is not None
    ]
    # Guards the walk above: a section numbered past it would go unchecked.
    assert len(found) == len(book)
    return found


def test_every_section_specifies_some_columns(book):
    assert [f"{s.file} {s.section}" for s in _sections(book) if not s.columns] == []


def test_every_column_is_a_data_column_with_a_name(book):
    # Column 1 holds the row labels. A range starting there, or a dim1 left
    # empty, publishes rows that no one can interpret.
    bad = [
        f"{s.file} {s.section} col {number}"
        for s in _sections(book)
        for number, column in s.columns.items()
        if number < 2 or column.column != number or not column.dim1.strip()
    ]
    assert bad == []


def test_every_file_stem_has_the_corpus_shape(book):
    # The table id is read from the stem, and verify finds the source file by
    # that id alone, so a stem with a typo or an extension in it would make a
    # table that extracts nothing or cannot be checked.
    shape = re.compile(r"[A-Za-z]+_Mt\d{3}(-\d)?")
    assert sorted(stem for stem in book.files() if not shape.fullmatch(stem)) == []


def test_no_two_files_share_a_table_id(book):
    # Two stems ending in the same id would be merged into one table in the
    # output, and verify would check both against whichever file it found.
    ids = [stem.split("_")[-1] for stem in book.files()]
    assert len(ids) == len(set(ids))


def test_add_range_keeps_a_dim2_set_earlier():
    # A range assigned after a column's dim2 renames the group; it must not
    # discard the label given for that one column.
    spec = SectionSpec("Test_Mt990", 1)
    spec.set_dim2(3, "男")
    spec.add_range(2, 4, "教員")
    assert spec.columns == {
        2: ColumnSpec(2, "教員", None),
        3: ColumnSpec(3, "教員", "男"),
        4: ColumnSpec(4, "教員", None),
    }


def test_set_dim2_keeps_the_dim1():
    spec = SectionSpec("Test_Mt990", 1)
    spec.add_range(2, 3, "教員")
    spec.set_dim2(3, "女")
    assert spec.columns[3] == ColumnSpec(3, "教員", "女")


def test_a_second_definition_of_a_section_keeps_its_dim2():
    book = SpecBook()
    book.define("Test_Mt990", 1, [(2, 3, "教員")], {3: "女"})
    book.define("Test_Mt990", 1, [(2, 3, "職員")])
    spec = book.get("Test_Mt990", 1)
    assert spec is not None
    assert spec.columns[3] == ColumnSpec(3, "職員", "女")
