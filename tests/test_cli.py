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
    assert len(frame) == 36_570
    assert "36,570 rows" in capsys.readouterr().out


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
    assert "1 mismatches" in captured.err


@pytest.mark.corpus
def test_notes_writes_a_csv(corpus, tmp_path, capsys):
    destination = tmp_path / "notes.csv"
    assert main(["notes", str(corpus), str(destination)]) == 0
    frame = pd.read_csv(destination)
    assert set(frame["kind"]) <= {"note", "source"}
    assert "notes from" in capsys.readouterr().out
