"""The worked example in docs/EXAMPLE.md, run as a test so it cannot rot.

Every number asserted here appears in that document. If this file needs
changing, the document needs changing with it.
"""

import ast
import re
from pathlib import Path

import pandas as pd
import pytest

from twstat import extract_corpus, verify
from twstat.notes import extract_notes
from twstat.spec import SpecBook

EXAMPLE = Path(__file__).resolve().parent.parent / "docs" / "EXAMPLE.md"


def document_rows() -> list[list[object]]:
    """The sheet exactly as docs/EXAMPLE.md builds it.

    Read out of the page rather than typed again here, so that editing the
    page's sheet without updating what it says about the sheet fails the suite.
    """
    text = EXAMPLE.read_text(encoding="utf-8")
    block = re.search(r"^rows = (\[.*?^\])$", text, re.MULTILINE | re.DOTALL)
    assert block, "docs/EXAMPLE.md no longer builds its sheet as `rows = [...]`"
    return ast.literal_eval(block.group(1))


@pytest.fixture
def example(tmp_path):
    pd.DataFrame(document_rows()).to_excel(tmp_path / "Demo_Mt900.xlsx", header=False, index=False)
    return tmp_path


@pytest.fixture
def book():
    spec = SpecBook()
    for number, group in [(1, "本省人"), (2, "日本人")]:
        spec.section("Demo_Mt900", number).add_range(2, 4, group)
    return spec


def test_the_example_extracts_fifteen_observations(example, book):
    tidy = extract_corpus(example, book)
    assert len(tidy) == 15
    assert set(tidy["section"]) == {1, 2}
    assert set(tidy["dim1"]) == {"本省人", "日本人"}
    assert set(tidy["dim2"]) == {"校數", "教員數", "學生數"}
    assert set(tidy["period_type"]) == {"fiscal_year_end"}
    assert sorted(tidy["year"].unique()) == [1899, 1900, 1901]


def test_the_example_reads_each_awkward_cell_as_documented(example, book):
    tidy = extract_corpus(example, book).set_index(["src_row", "src_col"])
    braced = tidy.loc[(6, 4)]
    assert braced["value"] == 69.0 and braced["flag"] == "bracket_artifact"
    absent = tidy.loc[(7, 3)]
    assert pd.isna(absent["value"]) and absent["flag"] == "missing"
    below_one = tidy.loc[(8, 2)]
    assert below_one["value"] == 0.0 and below_one["flag"] == "less_than_one_unit"


def test_the_example_verifies(example, book):
    assert verify(extract_corpus(example, book), example) == []


def test_a_missing_section_is_dropped_and_verification_still_passes(example):
    # The point of this half of the example. Specify one section of a sheet
    # that holds two and the second is not merged, it is simply absent, and
    # verify has nothing to complain about because every value it can see is
    # correct. Completeness is not what the verifier checks.
    half = SpecBook()
    half.section("Demo_Mt900", 1).add_range(2, 4, "學校")
    tidy = extract_corpus(example, half)
    assert len(tidy) == 9
    assert verify(tidy, example) == []


def test_the_example_footnote_is_attached_to_its_section(example):
    notes = extract_notes(example / "Demo_Mt900.xlsx")
    assert len(notes) == 1
    assert notes[0].section == 2
    assert notes[0].kind == "note"
