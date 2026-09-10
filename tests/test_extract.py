"""End-to-end extraction and verification."""

import pandas as pd
import pytest

from twstat import extract_file, verify
from twstat.spec import SpecBook
from twstat.values import Flag


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


def test_verify_accepts_a_faithful_extraction(flat_sheet, flat_spec, tmp_path):
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


def test_extract_corpus_skips_files_without_a_specification(flat_sheet, flat_spec):
    from twstat import extract_corpus

    tidy = extract_corpus(flat_sheet.parent, flat_spec)
    assert set(tidy["table_id"]) == {"Mt998"}


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
