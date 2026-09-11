"""The verifier's reach: what it checks, and what it refuses to let through.

These cover the rows with no value, which were not read back at all until
docs/WORK.md R02. A wrong coordinate on such a row used to be undetectable.
"""

import pandas as pd
import pytest

from twstat import extract_file, verify
from twstat.spec import SpecBook


@pytest.fixture
def tidy(flat_sheet):
    book = SpecBook()
    book.define("Test_Mt998", 1, [(2, 2, "校數"), (3, 3, "學生")])
    return extract_file(flat_sheet, book)


def test_a_missing_row_pointed_at_a_real_figure_is_caught(tidy, flat_sheet):
    missing = tidy.index[tidy["value"].isna()][0]
    present = tidy.index[tidy["value"].notna()][0]
    tidy.loc[missing, ["src_row", "src_col"]] = tidy.loc[present, ["src_row", "src_col"]].values
    reasons = [m.reason for m in verify(tidy, flat_sheet.parent)]
    assert len(reasons) == 1
    assert reasons[0].startswith("recorded absent but source reads")


def test_a_missing_row_pointed_off_the_sheet_is_caught(tidy, flat_sheet):
    missing = tidy.index[tidy["value"].isna()]
    tidy.loc[missing, "src_row"] = 9999
    reasons = [m.reason for m in verify(tidy, flat_sheet.parent)]
    assert reasons == ["out of range"] * len(missing)


@pytest.mark.parametrize("coordinate", [0, -1])
def test_a_coordinate_that_is_not_one_based_is_refused(tidy, flat_sheet, coordinate):
    # pandas would read row -1 as the last row of the sheet without complaint.
    tidy.loc[tidy.index[0], "src_row"] = coordinate
    reasons = [m.reason for m in verify(tidy, flat_sheet.parent)]
    assert reasons == ["coordinate is not 1-based"]


def test_a_value_wrong_in_its_last_place_is_caught(tidy, flat_sheet):
    target = tidy.index[tidy["value"] == 100.0][0]
    tidy.loc[target, "value"] = 100.5
    assert [m.reason for m in verify(tidy, flat_sheet.parent)] == ["100.0 != 100.5"]


def test_a_figure_claimed_as_braced_must_be_braced_in_the_source(tidy, flat_sheet):
    plain = tidy.index[(tidy["value"] == 100.0)][0]
    tidy.loc[plain, "flag"] = "bracket_artifact"
    reasons = [m.reason for m in verify(tidy, flat_sheet.parent)]
    assert len(reasons) == 1 and reasons[0].startswith("recorded as braced")


def test_floating_point_noise_is_not_a_mismatch(tidy, flat_sheet):
    # A value that has been through a CSV can come back different in its last
    # digit. That is not a mismatch.
    target = tidy[(tidy.year == 1922) & (tidy.dim1 == "學生")].index[0]
    tidy.loc[target, "value"] = 100.0 + 1e-12
    assert verify(tidy, flat_sheet.parent) == []


def test_the_xls_is_read_when_an_xlsx_of_the_same_table_is_beside_it(tmp_path):
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
