"""Command line behaviour, including its exit codes.

The extract, verify and notes commands are run twice over: against the real
corpus under the ``corpus`` marker, and against the small fixture sheets with
the 1946 specification book swapped out, so that CI, which has no corpus, still
runs every path through them.
"""

import pandas as pd
import pytest

from twstat.cli import main
from twstat.extract import COLUMNS
from twstat.spec import SpecBook


@pytest.fixture
def corpus(raw_dir):
    return raw_dir


@pytest.fixture
def small_corpus(flat_sheet, monkeypatch):
    # The command always uses the 1946 book; it is replaced here by one that
    # specifies the fixture sheet. main() imports build at call time, so
    # patching the module attribute is enough.
    book = SpecBook()
    book.define("Test_Mt998", 1, [(2, 2, "校數"), (3, 3, "學生")])
    monkeypatch.setattr("twstat.corpus1946.build", lambda: book)
    return flat_sheet.parent


def test_no_arguments_is_an_error():
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code != 0


def test_unknown_command_is_an_error():
    with pytest.raises(SystemExit) as exit_info:
        main(["frobnicate"])
    assert exit_info.value.code != 0


@pytest.mark.corpus
def test_extract_writes_a_csv(corpus, tmp_path, capsys):
    destination = tmp_path / "nested" / "tidy.csv"
    assert main(["extract", str(corpus), str(destination)]) == 0
    assert destination.exists()

    frame = pd.read_csv(destination)
    assert len(frame) == 39_150
    assert "39,150 rows" in capsys.readouterr().out


@pytest.mark.corpus
def test_verify_reports_success(corpus, tmp_path, capsys):
    destination = tmp_path / "tidy.csv"
    main(["extract", str(corpus), str(destination)])
    capsys.readouterr()

    assert main(["verify", str(destination), str(corpus)]) == 0
    assert "no mismatches" in capsys.readouterr().out


@pytest.mark.corpus
def test_verify_exits_non_zero_on_a_mismatch(corpus, tmp_path, capsys):
    destination = tmp_path / "tidy.csv"
    main(["extract", str(corpus), str(destination)])
    capsys.readouterr()

    frame = pd.read_csv(destination)
    frame.loc[frame[frame["value"].notna()].index[0], "value"] = 999_999.0
    frame.to_csv(destination, index=False, encoding="utf-8-sig")

    assert main(["verify", str(destination), str(corpus)]) == 1
    captured = capsys.readouterr()
    assert "999999" in captured.out
    assert "1 mismatch out of" in captured.err


@pytest.mark.corpus
def test_notes_writes_a_csv(corpus, tmp_path, capsys):
    destination = tmp_path / "notes.csv"
    assert main(["notes", str(corpus), str(destination)]) == 0
    frame = pd.read_csv(destination)
    assert set(frame["kind"]) <= {"note", "source"}
    assert "notes from" in capsys.readouterr().out


def test_sample_draws_a_reproducible_blank_sheet(tmp_path, capsys):
    tidy = pd.DataFrame(
        {
            "table_id": ["Mt1"] * 6 + ["Mt2"] * 6,
            "section": [1] * 9 + [2] * 3,
            "year": list(range(1900, 1906)) * 2,
            "src_row": list(range(1, 7)) * 2,
            "src_col": [2, 3, 4] * 4,
            "value": range(12),
            "dim1": ["甲"] * 12,
        }
    )
    source = tmp_path / "tidy.csv"
    tidy.to_csv(source, index=False)

    first = tmp_path / "a" / "sheet.csv"
    assert main(["sample", str(source), str(first), "--size", "6"]) == 0
    assert "seed 20260909" in capsys.readouterr().out

    second = tmp_path / "b.csv"
    assert main(["sample", str(source), str(second), "--size", "6"]) == 0
    drawn = pd.read_csv(first)
    assert drawn.equals(pd.read_csv(second))
    assert list(drawn.columns[-3:]) == ["coded_dim1", "coded_dim2", "note"]
    assert drawn[["coded_dim1", "coded_dim2"]].isna().all().all()


def test_a_different_seed_draws_a_different_sheet(tmp_path):
    tidy = pd.DataFrame(
        {
            "table_id": ["Mt1"] * 20,
            "section": [1] * 20,
            "year": range(1900, 1920),
            "src_row": range(1, 21),
            "src_col": [2] * 20,
            "value": range(20),
            "dim1": ["甲"] * 20,
        }
    )
    source = tmp_path / "tidy.csv"
    tidy.to_csv(source, index=False)
    one, two = tmp_path / "1.csv", tmp_path / "2.csv"
    main(["sample", str(source), str(one), "--size", "5", "--seed", "1"])
    main(["sample", str(source), str(two), "--size", "5", "--seed", "2"])
    assert not pd.read_csv(one).equals(pd.read_csv(two))


def test_notes_reads_xlsx_as_well_as_xls(tmp_path, capsys):
    # verify and extract_corpus each globbed only *.xls once, and each returned
    # nothing without complaining. This command was the third instance.
    rows = [
        ["表993 附註測試", None],
        ["1.第一區段", None],
        [None, "學生數"],
        ["十 一 年(1922)", 5],
        ["附註:(1)測試用的附註文字", None],
    ]
    pd.DataFrame(rows).to_excel(tmp_path / "Test_Mt993.xlsx", header=False, index=False)

    destination = tmp_path / "notes.csv"
    assert main(["notes", str(tmp_path), str(destination)]) == 0
    assert len(pd.read_csv(destination)) == 1
    assert "1 notes from 1 files" in capsys.readouterr().out


def test_extract_writes_the_specified_rows(small_corpus, tmp_path, capsys):
    destination = tmp_path / "out" / "tidy.csv"
    assert main(["extract", str(small_corpus), str(destination)]) == 0

    frame = pd.read_csv(destination)
    assert list(frame.columns) == COLUMNS
    assert list(zip(frame["src_row"], frame["src_col"], strict=True)) == [
        (3, 2),
        (3, 3),
        (4, 2),
        (4, 3),
        (5, 2),
        (5, 3),
    ]
    # Six rows, one of them the missing marker, so five carry a number.
    assert capsys.readouterr().out == f"{destination}: 6 rows, 5 values, 1 tables\n"


def test_verify_reports_success_on_a_faithful_file(small_corpus, tmp_path, capsys):
    destination = tmp_path / "tidy.csv"
    main(["extract", str(small_corpus), str(destination)])
    capsys.readouterr()

    assert main(["verify", str(destination), str(small_corpus)]) == 0
    assert capsys.readouterr().out == "5 values checked, no mismatches\n"


def test_verify_names_each_mismatch_and_exits_non_zero(small_corpus, tmp_path, capsys):
    destination = tmp_path / "tidy.csv"
    main(["extract", str(small_corpus), str(destination)])
    capsys.readouterr()

    frame = pd.read_csv(destination)
    frame.loc[(frame["src_row"] == 3) & (frame["src_col"] == 2), "value"] = 3.5
    frame.to_csv(destination, index=False, encoding="utf-8-sig")

    assert main(["verify", str(destination), str(small_corpus)]) == 1
    captured = capsys.readouterr()
    assert captured.out == "Mt998 r3 c2: 3.0 != 3.5\n"
    assert captured.err == "1 mismatch out of 5\n"


def test_verify_counts_several_mismatches(small_corpus, tmp_path, capsys):
    destination = tmp_path / "tidy.csv"
    main(["extract", str(small_corpus), str(destination)])
    frame = pd.read_csv(destination)
    frame.loc[frame["src_row"] == 3, "value"] += 1
    frame.to_csv(destination, index=False, encoding="utf-8-sig")
    capsys.readouterr()

    assert main(["verify", str(destination), str(small_corpus)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["Mt998 r3 c2: 3.0 != 4.0", "Mt998 r3 c3: 100.0 != 101.0"]
    assert captured.err == "2 mismatches out of 5\n"


def test_notes_writes_every_note_of_every_file(annotated_sheet, flat_sheet, tmp_path, capsys):
    # Both fixtures write into the same directory, which is the corpus here.
    destination = tmp_path / "out.csv"
    assert main(["notes", str(tmp_path), str(destination)]) == 0

    frame = pd.read_csv(destination, keep_default_na=False)
    assert list(frame.columns) == [
        "file",
        "table_id",
        "section",
        "section_label",
        "src_row",
        "kind",
        "text",
    ]
    assert frame.values.tolist() == [
        ["Test_Mt996", "Mt996", 1, "第一區段", 5, "note", "附註:(1)第一行說明接續的第二行說明文字"],
        ["Test_Mt996", "Mt996", 2, "第二區段", 10, "note", "註:短註"],
        ["Test_Mt996", "Mt996", 2, "第二區段", 11, "source", "材料來源:測試資料"],
        ["Test_Mt998", "Mt998", 1, "", 6, "source", "材料來源:測試用"],
    ]
    assert capsys.readouterr().out == f"{destination}: 4 notes from 2 files\n"
