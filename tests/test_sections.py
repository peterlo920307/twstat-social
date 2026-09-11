"""Detection of stacked tables."""

import pandas as pd
import pytest

from twstat.sections import find, header_rows


def test_unmarked_sheet_is_one_section(flat_sheet):
    frame = pd.read_excel(flat_sheet, header=None)
    sections = find(frame)
    assert len(sections) == 1
    assert sections[0].label is None
    assert sections[0].start == 0


def test_markers_split_the_sheet(stacked_sheet):
    frame = pd.read_excel(stacked_sheet, header=None)
    sections = find(frame)
    assert [s.number for s in sections] == [1, 2]
    assert sections[0].label == "1.本省人"
    assert sections[1].label == "2.日本人"


def test_sections_do_not_overlap_and_cover_the_tail(stacked_sheet):
    frame = pd.read_excel(stacked_sheet, header=None)
    sections = find(frame)
    assert sections[0].end == sections[1].start
    assert sections[-1].end == len(frame)


def test_each_section_has_its_own_header(stacked_sheet):
    frame = pd.read_excel(stacked_sheet, header=None)
    first, second = find(frame)
    first_data, first_headers = header_rows(frame, first)
    _, second_headers = header_rows(frame, second)
    assert first_headers and second_headers
    assert max(first_headers) < first_data
    assert min(second_headers) > first_data


def test_title_row_is_not_treated_as_a_header(flat_sheet):
    frame = pd.read_excel(flat_sheet, header=None)
    section = find(frame)[0]
    _, headers = header_rows(frame, section)
    assert 0 not in headers


def test_section_without_dates_reports_no_data_row(tmp_path):
    rows = [["表997 橫斷面", None], ["學校名稱", "學生數"], ["某某學校", 50]]
    path = tmp_path / "Test_Mt997.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    frame = pd.read_excel(path, header=None)
    first, headers = header_rows(frame, find(frame)[0])
    assert first is None and headers == []


def test_a_specification_book_reports_how_many_sections_it_holds():
    from twstat.spec import SpecBook

    book = SpecBook()
    assert len(book) == 0
    book.section("Test_Mt998", 1).add_range(2, 3, "校數")
    book.section("Test_Mt998", 2).add_range(2, 3, "學生數")
    assert len(book) == 2


@pytest.mark.parametrize("stop", [".", "．"])
def test_section_markers_are_found_with_either_full_stop(tmp_path, stop):
    # The full-width U+FF0E is used interchangeably with the ASCII period in
    # this compendium and looks identical in print. Only the ASCII form was
    # accepted until docs/W06_layout.md, and the two sections below were read
    # as one: every figure correct, every attribution wrong.
    rows = [
        ["表995 全形標記測試", None],
        [f"1{stop}官等", None],
        [None, "人數"],
        ["十 一 年(1922)", 10],
        [f"2{stop}性別", None],
        [None, "人數"],
        ["十 一 年(1922)", 20],
    ]
    path = tmp_path / "Test_Mt995.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    frame = pd.read_excel(path, header=None)
    assert [s.number for s in find(frame)] == [1, 2]


def test_a_decimal_number_is_not_a_section_marker(tmp_path):
    rows = [["表994", None], ["1.5", 3], ["十 一 年(1922)", 10]]
    path = tmp_path / "Test_Mt994.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    frame = pd.read_excel(path, header=None)
    assert len(find(frame)) == 1


def _frame(tmp_path, rows):
    path = tmp_path / "Test_Mt990.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return pd.read_excel(path, header=None)


def test_header_rows_are_exactly_the_rows_with_column_text(tmp_path):
    # The title carries a unit note at the right, so it has text beyond
    # column 0 and would pass as a heading if its 表 were not checked. The unit
    # note in row 4 sits in column 0 only; a row is a heading because of text
    # over the data columns, and column 0 is where the row labels live.
    rows = [
        ["表990 標題測試", None, None, "(單位:人)"],
        [None, "公", None, "立"],
        [None, "校數", "教員數", "學生數"],
        ["單位:人", None, None, None],
        ["十 一 年(1922)", 1, 10, 100],
    ]
    frame = _frame(tmp_path, rows)
    assert header_rows(frame, find(frame)[0]) == (4, [1, 2])


def test_a_marker_row_is_not_a_header_row(tmp_path):
    # Both markers carry text to their right. The first sits above a real
    # heading; the second part has no heading of its own, so if the marker row
    # were taken as one it would be the innermost header and its text would
    # become dim2.
    rows = [
        ["表990 標記測試", None, None, None],
        ["1.本省人", None, None, "(單位:人)"],
        [None, "校數", "教員數", "學生數"],
        ["十 一 年(1922)", 1, 10, 100],
        ["2.日本人", None, "(續)", None],
        ["十 一 年(1922)", 2, 20, 200],
    ]
    frame = _frame(tmp_path, rows)
    first, second = find(frame)
    assert header_rows(frame, first) == (3, [2])
    assert header_rows(frame, second) == (5, [])


def test_a_long_numbered_sentence_is_a_footnote_not_a_section(tmp_path):
    # A numbered footnote line has the shape of a marker: digit, stop, text.
    # Length is what separates them. The longest heading in the 1946 corpus is
    # 18 characters and nothing there of this shape reaches forty, so only this
    # test holds the limit in place.
    sentence = "2.本表所列學生數係指各年度末在學之學生不含已退學休學及轉學之學生亦不含選科生聽講生"
    rows = [
        ["表990 長句測試", None],
        ["1.本省人", None],
        [None, "學生數"],
        ["十 一 年(1922)", 5],
        [sentence, None],
    ]
    frame = _frame(tmp_path, rows)
    sections = find(frame)
    assert [(s.label, s.start, s.end) for s in sections] == [("1.本省人", 1, 5)]
