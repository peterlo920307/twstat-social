"""Corrections the specification can make to the source, and their guard.

Two exist in the 1946 compendium: a Gregorian year printed wrongly, and a table
whose own footnote overrides the compilers' general reading of a printed 0.
"""

import pandas as pd
import pytest

from twstat import extract_file
from twstat.spec import SpecBook


def _sheet(tmp_path, name, rows):
    path = tmp_path / name
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path


@pytest.fixture
def misprinted(tmp_path):
    return _sheet(
        tmp_path,
        "Test_Mt980.xlsx",
        [
            ["表980 誤植測試", None],
            [None, "人數"],
            ["十    年(1902)", 5],
            ["九    年(1093)", 6],
            ["八    年(1904)", 7],
        ],
    )


def test_a_row_that_looks_dated_but_gives_no_year_is_refused(misprinted):
    # Welfare_Mt504 printed 1903 as (1093), and the row used to vanish without
    # a word. The one internal gap in the published coverage was this misprint.
    book = SpecBook()
    book.define("Test_Mt980", 1, [(2, 2, "人數")])
    with pytest.raises(ValueError, match="row 4"):
        extract_file(misprinted, book)


def test_a_corrected_year_puts_the_row_back(misprinted):
    book = SpecBook()
    book.define("Test_Mt980", 1, [(2, 2, "人數")])
    book.correct_year("Test_Mt980", 4, 1903, "between 1902 and 1904")
    tidy = extract_file(misprinted, book)
    assert tidy["year"].tolist() == [1902, 1903, 1904]
    assert tidy.loc[tidy["year"] == 1903, "value"].tolist() == [6.0]
    assert book.corrected_year("Test_Mt980", 4) == 1903
    assert book.corrected_year("Test_Mt980", 3) is None


def test_a_printed_zero_is_below_one_unit_unless_the_table_says_otherwise(tmp_path):
    path = _sheet(
        tmp_path,
        "Test_Mt979.xlsx",
        [["表979 零測試", None], [None, "死亡率"], ["十 一 年(1922)", 0]],
    )
    book = SpecBook()
    book.define("Test_Mt979", 1, [(2, 2, "死亡率")])
    assert extract_file(path, book)["flag"].tolist() == ["less_than_one_unit"]

    book.zero_is_exact("Test_Mt979", 1)
    tidy = extract_file(path, book)
    assert tidy["value"].tolist() == [0.0]
    assert tidy["flag"].isna().all()


@pytest.mark.parametrize("stop", [".", "．"])
def test_the_section_label_loses_its_marker_and_any_private_use_characters(tmp_path, stop):
    path = _sheet(
        tmp_path,
        f"Test_Mt97{'8' if stop == '.' else '7'}.xlsx",
        [
            ["表978 標籤測試", None],
            [f"1{stop}民國二十年至三十一年(2)\uf6b2", None],
            [None, "人數"],
            ["十 一 年(1922)", 10],
        ],
    )
    book = SpecBook()
    book.define(path.stem, 1, [(2, 2, "人數")])
    assert extract_file(path, book)["section_label"].tolist() == ["民國二十年至三十一年(2)"]
