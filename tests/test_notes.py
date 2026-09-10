"""Recovery of the compilers' footnotes."""

import pandas as pd

from twstat.notes import extract_notes


def test_finds_notes_and_source_attributions(annotated_sheet):
    notes = extract_notes(annotated_sheet)
    kinds = [note.kind for note in notes]
    assert kinds.count("note") == 2
    assert kinds.count("source") == 1


def test_joins_a_note_that_runs_onto_the_next_line(annotated_sheet):
    notes = extract_notes(annotated_sheet)
    first = next(note for note in notes if note.text.startswith("附註"))
    assert "第一行說明" in first.text
    assert "接續的第二行說明文字" in first.text


def test_attributes_each_note_to_its_section(annotated_sheet):
    notes = extract_notes(annotated_sheet)
    by_section = {note.section for note in notes}
    assert by_section == {1, 2}
    assert all(note.section_label for note in notes)


def test_section_marker_is_stripped_from_the_label(annotated_sheet):
    notes = extract_notes(annotated_sheet)
    assert all(not note.section_label[0].isdigit() for note in notes)


def test_records_where_the_note_was_found(annotated_sheet):
    frame = pd.read_excel(annotated_sheet, header=None)
    for note in extract_notes(annotated_sheet):
        cell = str(frame.iat[note.src_row - 1, 0])
        assert note.text.startswith(cell.replace(" ", "")[:4])


def test_table_id_comes_from_the_file_name(annotated_sheet):
    assert {note.table_id for note in extract_notes(annotated_sheet)} == {"Mt996"}


def test_a_sheet_without_notes_yields_nothing(flat_sheet, tmp_path):
    rows = [[None, "校數"], ["十 一 年(1922)", 3]]
    path = tmp_path / "Test_Mt995.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    assert extract_notes(path) == []


def test_a_following_note_does_not_get_absorbed(annotated_sheet):
    # 材料來源 sits directly under 註; they must stay separate.
    texts = [note.text for note in extract_notes(annotated_sheet)]
    assert any(text.startswith("材料來源") for text in texts)
    assert not any("材料來源" in text and text.startswith("註") for text in texts)
