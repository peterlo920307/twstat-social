"""Command line behaviour, including its exit codes."""

import pandas as pd
import pytest

from twstat.cli import main


@pytest.fixture
def corpus(raw_dir):
    return raw_dir


def test_no_arguments_is_an_error(capsys):
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
    assert len(frame) == 36_672
    assert "36,672 rows" in capsys.readouterr().out


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
