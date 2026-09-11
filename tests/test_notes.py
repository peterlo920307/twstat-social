"""Recovery of the compilers' footnotes.

Every note in the 1946 corpus ends at a blank row, at the end of the sheet, or
at the head of the next note. The other stopping rules below (a dated row, a
short heading, a section marker) and the search beyond column 0 are never
reached by a real file, so these tests are the only thing that holds them in
place. They compare whole texts rather than substrings because a note that
swallows the line after it still contains everything it should.
"""

import pandas as pd
import pytest

from twstat.notes import extract_notes


def _write(tmp_path, rows, name="Test_Mt990.xlsx"):
    path = tmp_path / name
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path


def _summary(path):
    return [
        (note.section, note.section_label, note.src_row, note.kind, note.text)
        for note in extract_notes(path)
    ]


def test_reads_every_note_of_the_annotated_sheet_exactly(annotated_sheet):
    assert _summary(annotated_sheet) == [
        (1, "第一區段", 5, "note", "附註:(1)第一行說明接續的第二行說明文字"),
        (2, "第二區段", 10, "note", "註:短註"),
        (2, "第二區段", 11, "source", "材料來源:測試資料"),
    ]


def test_a_note_stops_at_the_next_section_marker(annotated_sheet):
    # The first note is followed by its continuation line and then, with no
    # blank row between, by 2.第二區段. The heading is long enough to pass for
    # a continuation, and before the marker check it was appended to the note.
    first = extract_notes(annotated_sheet)[0]
    assert first.text == "附註:(1)第一行說明接續的第二行說明文字"


def test_a_following_note_does_not_get_absorbed(annotated_sheet):
    # 材料來源 sits directly under 註; they must stay separate.
    texts = [note.text for note in extract_notes(annotated_sheet)]
    assert texts[1:] == ["註:短註", "材料來源:測試資料"]


def test_records_where_the_note_was_found(annotated_sheet):
    frame = pd.read_excel(annotated_sheet, header=None)
    for note in extract_notes(annotated_sheet):
        cell = str(frame.iat[note.src_row - 1, 0])
        assert note.text.startswith(cell.replace(" ", ""))


def test_table_id_comes_from_the_file_name(annotated_sheet):
    assert {note.table_id for note in extract_notes(annotated_sheet)} == {"Mt996"}
    assert {note.file for note in extract_notes(annotated_sheet)} == {"Test_Mt996"}


def test_a_sheet_without_notes_yields_nothing(tmp_path):
    rows = [[None, "校數"], ["十 一 年(1922)", 3]]
    assert extract_notes(_write(tmp_path, rows, "Test_Mt995.xlsx")) == []


def test_a_note_is_found_in_the_fourth_column(tmp_path):
    # A note indented into the body of the table is still a note. The four
    # leftmost columns are searched, so the head is found here in column 4.
    rows = [
        ["表990 附註位置測試", None, None, None],
        [None, "學生數", None, None],
        ["十 一 年(1922)", 5, None, None],
        [None, None, None, "註:本欄不含分校"],
    ]
    assert _summary(_write(tmp_path, rows)) == [(1, "", 4, "note", "註:本欄不含分校")]


def test_a_short_line_after_a_note_is_a_heading_not_a_continuation(tmp_path):
    # An unnumbered heading for the next block has no marker to stop the note.
    # A line under four characters is taken for such a heading rather than for
    # more of the note; 高砂族 has three.
    rows = [
        ["表990 附註測試", None],
        [None, "學生數"],
        ["十 一 年(1922)", 5],
        ["附註:(1)本表數字係年度末現在數", None],
        ["高 砂 族", None],
        [None, "學生數"],
        ["十 一 年(1922)", 2],
    ]
    assert [note.text for note in extract_notes(_write(tmp_path, rows))] == [
        "附註:(1)本表數字係年度末現在數"
    ]


def test_a_dated_row_after_a_note_is_data_not_a_continuation(tmp_path):
    # A note printed between two rows of a series, to mark where the basis of
    # the figures changed, is followed directly by the next dated row. The
    # label is long enough to be taken for more of the note.
    rows = [
        ["表990 附註測試", None],
        [None, "學生數"],
        ["十 一 年(1922)", 5],
        ["註:以下改依新制計算", None],
        ["十 二 年(1923)", 7],
    ]
    assert [note.text for note in extract_notes(_write(tmp_path, rows))] == ["註:以下改依新制計算"]


def test_a_line_joined_to_a_note_is_not_searched_again(tmp_path):
    # Only column 0 is joined, but the head search looks at four columns. If
    # the rows already consumed as continuation were searched again, a cell to
    # the right that happens to open with 按 (or 註, or 說明) would be reported
    # as a note of its own.
    rows = [
        ["表990 附註測試", None, None],
        [None, "學生數", None],
        ["十 一 年(1922)", 5, None],
        ["附註:(1)本表學生數包括", None, None],
        ["選科生及聽講生在內", None, "按學年計"],
    ]
    assert _summary(_write(tmp_path, rows)) == [
        (1, "", 4, "note", "附註:(1)本表學生數包括選科生及聽講生在內")
    ]


@pytest.mark.parametrize("stop", [".", "．"])
def test_section_label_is_clean_with_either_full_stop(tmp_path, stop):
    # The marker pattern accepts the full-width U+FF0E as well as the ASCII
    # period. Stripping only the ASCII one from the label left "．官等".
    rows = [
        ["表995 全形標記測試", None],
        [f"1{stop}官等", None],
        [None, "人數"],
        ["十 一 年(1922)", 10],
        ["註:官等依當年制度", None],
        [f"2{stop}性別", None],
        [None, "人數"],
        ["十 一 年(1922)", 20],
        ["註:性別不詳者未列", None],
    ]
    notes = extract_notes(_write(tmp_path, rows, "Test_Mt995.xlsx"))
    assert [(note.section, note.section_label) for note in notes] == [(1, "官等"), (2, "性別")]
