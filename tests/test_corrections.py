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


@pytest.fixture
def paired(tmp_path):
    # The layout of Mt487-2 and Mt489: each year split across two rows by a
    # brace in the label column, only the first carrying the year.
    return _sheet(
        tmp_path,
        "Test_Mt976.xlsx",
        [
            ["表976 患者死亡測試", None, None],
            [None, "傷寒", "赤痢"],
            ["民國  二  十年(1931)┌患者", 762, 46],
            ["                   └死亡", 154, "."],
            ["      二十一年(1932)┌患者", 667, 60],
            ["                   └死亡", 128, 4],
        ],
    )


def test_the_second_row_of_a_pair_takes_the_year_of_the_first(paired):
    book = SpecBook()
    book.define("Test_Mt976", 1, [(2, 2, "傷寒"), (3, 3, "赤痢")], {2: "", 3: ""})
    tidy = extract_file(paired, book)
    typhoid = tidy[tidy["dim1"] == "傷寒"].set_index(["year", "dim2"])["value"]
    assert typhoid.to_dict() == {
        (1931, "患者"): 762.0,
        (1931, "死亡"): 154.0,
        (1932, "患者"): 667.0,
        (1932, "死亡"): 128.0,
    }


def test_a_missing_figure_in_the_second_row_keeps_its_row(paired):
    book = SpecBook()
    book.define("Test_Mt976", 1, [(2, 2, "傷寒"), (3, 3, "赤痢")], {2: "", 3: ""})
    tidy = extract_file(paired, book)
    row = tidy[(tidy["dim1"] == "赤痢") & (tidy["year"] == 1931) & (tidy["dim2"] == "死亡")]
    assert row["flag"].tolist() == ["missing"]


def test_a_braced_row_with_nothing_before_it_is_not_given_a_year(tmp_path):
    # An orphan └ row must not borrow a date from further up the sheet.
    path = _sheet(
        tmp_path,
        "Test_Mt975.xlsx",
        [
            ["表975", None],
            [None, "人數"],
            ["十 一 年(1922)", 5],
            ["        └死亡", 1],
        ],
    )
    book = SpecBook()
    book.define("Test_Mt975", 1, [(2, 2, "人數")])
    assert extract_file(path, book)["year"].tolist() == [1922]


def test_a_row_dimension_joins_a_column_one_rather_than_replacing_it(paired):
    book = SpecBook()
    book.define("Test_Mt976", 1, [(2, 2, "傷寒")], {2: "本省人"})
    tidy = extract_file(paired, book)
    assert set(tidy["dim2"]) == {"本省人·患者", "本省人·死亡"}


@pytest.fixture
def braced(tmp_path):
    # Table 507's layout: a figure printed across three columns sits in the
    # first of them, and the two it spans are left empty.
    return _sheet(
        tmp_path,
        "Test_Mt972.xlsx",
        [
            ["表972 括弧跨欄測試", None, None, None, None],
            [None, "寺廟", "齋堂", "神明會", "其他"],
            ["民國前三年底(1909)", "└────646────┘", None, None, None],
            ["二年底(1910)", 749, 3, ".", None],
            ["一年底(1911)", "└─.─┘", None, 5, 6],
        ],
    )


def _flags(path, stem):
    book = SpecBook()
    book.define(stem, 1, [(2, 2, "寺廟"), (3, 3, "齋堂"), (4, 4, "神明會"), (5, 5, "其他")])
    tidy = extract_file(path, book)
    return {(r.year, r.dim1): (r.value, r.flag) for r in tidy.itertuples()}


def test_the_columns_a_braced_figure_spans_are_covered_not_missing(braced):
    flags = _flags(braced, "Test_Mt972")
    assert flags[(1909, "寺廟")] == (646.0, "bracket_artifact")
    assert flags[(1909, "齋堂")][1] == "covered"
    assert flags[(1909, "神明會")][1] == "covered"
    assert flags[(1909, "其他")][1] == "covered"


def test_an_empty_cell_after_a_plain_figure_is_blank_and_a_dot_is_missing(braced):
    flags = _flags(braced, "Test_Mt972")
    assert flags[(1910, "神明會")][1] == "missing"
    assert flags[(1910, "其他")][1] == "blank"


def test_a_braced_missing_mark_covers_the_cells_it_spans(braced):
    flags = _flags(braced, "Test_Mt972")
    assert flags[(1911, "寺廟")][1] == "missing"
    assert flags[(1911, "齋堂")][1] == "covered"
    value, flag = flags[(1911, "神明會")]
    assert value == 5.0 and pd.isna(flag)


def test_verify_holds_each_empty_flag_to_what_the_cell_contains(braced):
    from twstat import verify

    book = SpecBook()
    book.define("Test_Mt972", 1, [(2, 2, "寺廟"), (3, 3, "齋堂"), (4, 4, "神明會"), (5, 5, "其他")])
    tidy = extract_file(braced, book)
    assert verify(tidy, braced.parent) == []
    covered = tidy.index[tidy["flag"] == "covered"][0]
    tidy.loc[covered, "flag"] = "missing"
    reasons = [m.reason for m in verify(tidy, braced.parent)]
    assert reasons == ["recorded as the missing mark but the source cell is empty"]
