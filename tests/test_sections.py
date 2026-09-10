"""Detection of stacked tables."""

import pandas as pd

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
    second_data, second_headers = header_rows(frame, second)
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
