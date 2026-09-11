"""End-to-end extraction and verification."""

from pathlib import Path

import pandas as pd
import pytest

from twstat import extract_file, verify
from twstat.spec import SpecBook
from twstat.values import Flag
from twstat.verify import Mismatch


@pytest.fixture
def flat_spec() -> SpecBook:
    book = SpecBook()
    book.define("Test_Mt998", 1, [(2, 2, "校數"), (3, 3, "學生")])
    return book


def test_extracts_one_row_per_value(flat_sheet, flat_spec):
    tidy = extract_file(flat_sheet, flat_spec)
    assert set(tidy["year"]) == {1922, 1923, 1924}
    assert set(tidy["dim1"]) == {"校數", "學生"}
    assert len(tidy) == 6


def test_records_the_originating_cell(flat_sheet, flat_spec):
    tidy = extract_file(flat_sheet, flat_spec)
    row = tidy[(tidy.year == 1922) & (tidy.dim1 == "學生")].iloc[0]
    frame = pd.read_excel(flat_sheet, header=None)
    assert frame.iat[row.src_row - 1, row.src_col - 1] == row.value


def test_missing_and_below_one_unit_stay_distinct(flat_sheet, flat_spec):
    tidy = extract_file(flat_sheet, flat_spec)
    flags = dict(zip(tidy.dim1 + "/" + tidy.year.astype(str), tidy.flag, strict=True))
    assert flags["校數/1923"] == Flag.MISSING.value
    assert flags["學生/1923"] == Flag.LESS_THAN_ONE_UNIT.value


def test_bracket_artifact_is_unwrapped(flat_sheet, flat_spec):
    tidy = extract_file(flat_sheet, flat_spec)
    row = tidy[(tidy.year == 1924) & (tidy.dim1 == "校數")].iloc[0]
    assert row.value == 7.0
    assert row.flag == Flag.BRACKET_ARTIFACT.value


def test_footnote_row_is_not_extracted(flat_sheet, flat_spec):
    tidy = extract_file(flat_sheet, flat_spec)
    assert tidy["year"].notna().all()
    assert 1925 not in set(tidy["year"])


def test_stacked_sections_stay_separate(stacked_sheet):
    book = SpecBook()
    book.define("Test_Mt999", [1, 2], [(2, 4, "教員")])
    tidy = extract_file(stacked_sheet, book)

    assert set(tidy["section"]) == {1, 2}
    assert set(tidy["section_label"]) == {"本省人", "日本人"}

    # The same year appears once per section, with different values.
    year_1922 = tidy[(tidy.year == 1922) & (tidy.dim2 == "共計")]
    assert len(year_1922) == 2
    assert set(year_1922["value"]) == {10.0, 20.0}


def test_dim2_comes_from_the_innermost_header(stacked_sheet):
    book = SpecBook()
    book.define("Test_Mt999", [1, 2], [(2, 4, "教員")])
    tidy = extract_file(stacked_sheet, book)
    assert set(tidy["dim2"]) == {"共計", "男", "女"}


def test_specification_overrides_the_header(stacked_sheet):
    book = SpecBook()
    book.define("Test_Mt999", [1, 2], [(2, 4, "教員")], {2: "総計"})
    tidy = extract_file(stacked_sheet, book)
    assert "総計" in set(tidy["dim2"])


def test_empty_specification_suppresses_dim2(stacked_sheet):
    book = SpecBook()
    book.define("Test_Mt999", [1, 2], [(2, 4, "教員")], {2: ""})
    tidy = extract_file(stacked_sheet, book)
    assert tidy[tidy.src_col == 2]["dim2"].isna().all()


def test_unspecified_file_yields_nothing(flat_sheet):
    assert len(extract_file(flat_sheet, SpecBook())) == 0


def test_verify_accepts_a_faithful_extraction(flat_sheet, flat_spec):
    tidy = extract_file(flat_sheet, flat_spec)
    assert verify(tidy, flat_sheet.parent) == []


def test_verify_catches_a_corrupted_value(flat_sheet, flat_spec):
    tidy = extract_file(flat_sheet, flat_spec)
    target = tidy[tidy["value"].notna()].index[0]
    tidy.loc[target, "value"] = 999.0
    mismatches = verify(tidy, flat_sheet.parent)
    assert len(mismatches) == 1
    assert "999" in mismatches[0].reason


def test_verify_ignores_rows_with_no_value(flat_sheet, flat_spec):
    # A missing marker has nothing to compare against; it must not be reported.
    tidy = extract_file(flat_sheet, flat_spec)
    assert tidy["value"].isna().any()
    assert verify(tidy, flat_sheet.parent) == []


def test_verify_refuses_to_pass_when_the_source_is_missing(flat_sheet, flat_spec, tmp_path):
    # Returning an empty list for input that was never read would be worse than
    # any mismatch it could report.
    from twstat.verify import SourceNotFoundError

    tidy = extract_file(flat_sheet, flat_spec)
    empty = tmp_path / "elsewhere"
    empty.mkdir()
    with pytest.raises(SourceNotFoundError):
        verify(tidy, empty)


def test_verify_does_not_flag_bracket_artifacts(flat_sheet, flat_spec):
    # The verifier once compared raw cells with float() and reported └─7─┘ as an
    # error. It must apply the same parsing rules the extraction used.
    tidy = extract_file(flat_sheet, flat_spec)
    assert verify(tidy, flat_sheet.parent) == []


def test_verify_reports_a_coordinate_outside_the_sheet(flat_sheet, flat_spec):
    tidy = extract_file(flat_sheet, flat_spec)
    tidy.loc[tidy.index[0], "src_row"] = 9999
    mismatches = verify(tidy, flat_sheet.parent)
    assert [m.reason for m in mismatches] == ["out of range"]


def test_verify_reports_a_cell_it_cannot_parse(flat_sheet, flat_spec):
    # Point a row at the title cell, which holds text where a number should be.
    tidy = extract_file(flat_sheet, flat_spec)
    target = tidy[tidy["value"].notna()].index[0]
    tidy.loc[target, "src_row"] = 1
    tidy.loc[target, "src_col"] = 1
    mismatches = verify(tidy, flat_sheet.parent)
    assert len(mismatches) == 1
    assert "unparsable" in mismatches[0].reason


def test_extract_ignores_columns_beyond_the_sheet(flat_sheet):
    book = SpecBook()
    book.define("Test_Mt998", 1, [(2, 2, "校數"), (99, 99, "不存在的欄")])
    tidy = extract_file(flat_sheet, book)
    assert set(tidy["dim1"]) == {"校數"}


def test_extract_corpus_skips_files_without_a_specification(flat_sheet, flat_spec, monkeypatch):
    # A file with no specification must not even be opened: a directory of
    # source files can hold anything, and here it holds a file that is not a
    # spreadsheet at all under a name that looks like one.
    from twstat import extract_corpus

    (flat_sheet.parent / "Broken_Mt000.xlsx").write_bytes(b"not a spreadsheet")
    opened = []
    read_excel = pd.read_excel

    def spy(path, *args, **kwargs):
        opened.append(Path(path).name)
        return read_excel(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_excel", spy)
    tidy = extract_corpus(flat_sheet.parent, flat_spec)
    assert opened == [flat_sheet.name]
    assert set(tidy["table_id"]) == {"Mt998"}
    assert len(tidy) == 6


def test_extract_corpus_returns_empty_frame_when_nothing_matches(tmp_path):
    from twstat import extract_corpus
    from twstat.extract import COLUMNS

    empty = extract_corpus(tmp_path, SpecBook())
    assert len(empty) == 0
    assert list(empty.columns) == COLUMNS


def test_extract_file_skips_sections_that_have_no_specification(stacked_sheet):
    # Only the first of the sheet's two sections is specified. The second is
    # passed over rather than guessed at.
    book = SpecBook()
    book.section(stacked_sheet.stem, 1).add_range(2, 4, "本省人")
    tidy = extract_file(stacked_sheet, book)
    assert set(tidy["section"]) == {1}


def test_verify_reports_a_difference_of_half_a_unit(flat_sheet, flat_spec):
    # The tolerance exists for floating-point noise, not for rounding. Half a
    # unit is a transcription error and must be reported, with both numbers.
    tidy = extract_file(flat_sheet, flat_spec)
    target = tidy[(tidy.year == 1922) & (tidy.dim1 == "校數")].index[0]
    tidy.loc[target, "value"] = 3.5
    assert verify(tidy, flat_sheet.parent) == [Mismatch("Mt998", 3, 2, "3.0 != 3.5")]


def test_verify_tolerates_floating_point_noise(flat_sheet, flat_spec):
    # A value that has been through a CSV can come back different in its last
    # digit. That is not a mismatch.
    tidy = extract_file(flat_sheet, flat_spec)
    target = tidy[(tidy.year == 1922) & (tidy.dim1 == "學生")].index[0]
    tidy.loc[target, "value"] = 100.0 + 1e-12
    assert verify(tidy, flat_sheet.parent) == []


def test_verify_reads_the_xls_when_an_xlsx_of_the_same_table_is_beside_it(tmp_path):
    # The corpus is distributed as .xls. An .xlsx of the same table in the
    # same directory is a local conversion, possibly edited, and the numbers
    # are to be checked against the original. pandas cannot write .xls, but
    # read_excel chooses its reader from the file's contents rather than its
    # name, so an .xlsx written under the .xls name stands in for one.
    table = [["表990 來源測試", None], [None, "學生數"], ["十 一 年(1922)", 5]]
    converted = [["表990 來源測試", None], [None, "學生數"], ["十 一 年(1922)", 6]]
    original = tmp_path / "Test_Mt990.xls"
    pd.DataFrame(table).to_excel(tmp_path / "staging.xlsx", header=False, index=False)
    (tmp_path / "staging.xlsx").rename(original)
    pd.DataFrame(converted).to_excel(tmp_path / "Test_Mt990.xlsx", header=False, index=False)

    book = SpecBook()
    book.define("Test_Mt990", 1, [(2, 2, "學生")])
    tidy = extract_file(original, book)
    assert list(tidy["value"]) == [5.0]
    assert verify(tidy, tmp_path) == []


def _write(tmp_path, rows, name="Test_Mt990.xlsx"):
    path = tmp_path / name
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path


def test_a_marker_row_does_not_supply_dim2(tmp_path):
    # The second part has no heading of its own, and its marker row carries a
    # note to the right. Taken as a header row, that note would be the
    # innermost header and would label the column.
    rows = [
        ["表990 標記測試", None, None],
        ["1.本省人", None, None],
        [None, "校數", "學生數"],
        ["十 一 年(1922)", 1, 100],
        ["2.日本人", None, "(續)"],
        ["十 一 年(1922)", 2, 200],
    ]
    book = SpecBook()
    book.define("Test_Mt990", [1, 2], [(2, 3, "學校")])
    tidy = extract_file(_write(tmp_path, rows), book)
    assert list(tidy[tidy.section == 1]["dim2"]) == ["校數", "學生數"]
    assert "(續)" not in set(tidy["dim2"].dropna())


def test_a_unit_note_in_the_label_column_does_not_displace_the_header(tmp_path):
    # A unit note between the heading and the first year has text in column 0
    # only. Counted as a header row it would become the innermost one, and
    # every column would lose its dim2.
    rows = [
        ["表990 單位列測試", None, None],
        [None, "校數", "學生數"],
        ["(單位:人)", None, None],
        ["十 一 年(1922)", 3, 100],
    ]
    book = SpecBook()
    book.define("Test_Mt990", 1, [(2, 3, "公立")])
    tidy = extract_file(_write(tmp_path, rows), book)
    assert list(tidy["dim2"]) == ["校數", "學生數"]


@pytest.mark.parametrize(
    "stop",
    [
        ".",
        pytest.param(
            "．",
            marks=pytest.mark.xfail(
                strict=False,
                reason="extract.py strips only the ASCII stop from the label; "
                "the fix is being made there separately",
            ),
        ),
    ],
)
def test_section_label_is_clean_with_either_full_stop(tmp_path, stop):
    # Both stops are accepted as markers (tests/test_sections.py), so both
    # have to be removed from the label; otherwise the full-width one leaves
    # "．官等" in every row of the section.
    rows = [
        ["表995 全形標記測試", None],
        [f"1{stop}官等", None],
        [None, "人數"],
        ["十 一 年(1922)", 10],
        [f"2{stop}性別", None],
        [None, "人數"],
        ["十 一 年(1922)", 20],
    ]
    book = SpecBook()
    book.define("Test_Mt995", [1, 2], [(2, 2, "人數")])
    tidy = extract_file(_write(tmp_path, rows, "Test_Mt995.xlsx"), book)
    assert list(tidy["section_label"]) == ["官等", "性別"]
