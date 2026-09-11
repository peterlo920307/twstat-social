"""Checks against the real corpus. Skipped when the source files are absent."""

from pathlib import Path

import pandas as pd
import pytest

from twstat import extract_corpus, verify
from twstat.corpus1946 import build

pytestmark = pytest.mark.corpus

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def tidy(raw_dir):
    return extract_corpus(raw_dir, build())


def test_expected_shape(tidy):
    # These move whenever a reading rule changes, and each move is recorded in
    # the changelog. The last three: the brace pattern was widened, footnote
    # markers stopped disqualifying a figure, and three health tables were split
    # into the header bands they actually contain.
    assert len(tidy) == 39_150
    assert tidy["table_id"].nunique() == 48
    assert tidy.groupby(["table_id", "section"]).ngroups == 78


def test_every_value_matches_its_source_cell(tidy, raw_dir):
    assert verify(tidy, raw_dir) == []


def test_years_lie_inside_the_colonial_period(tidy):
    assert tidy["year"].min() == 1897
    assert tidy["year"].max() == 1945


def test_no_fragmented_labels_survive(tidy):
    # A single-character dimension usually means a scattered header was not
    # reassembled. 癌 is the exception: it is a whole disease name, printed
    # between 其他傳染病及寄生蟲病 and 其他惡性腫瘍 in three of the health tables.
    short = [label for label in tidy["dim1"].dropna().unique() if len(label) <= 1]
    assert short == ["癌"]


def test_period_types_are_all_recognised(tidy):
    assert not tidy["period_type"].isna().any()


def test_specification_covers_every_downloaded_file(raw_dir):
    book = build()
    stems = {path.stem for path in raw_dir.glob("*.xls")}
    # Two files are cross-sectional and deliberately excluded.
    assert stems - book.files() == {"Edu_Mt467", "Hygiene_Mt496"}


def test_the_committed_dataset_is_what_the_package_produces(tidy):
    # data/tidy.csv drifted from the code once already, which is how it came to
    # be missing 102 values and to use a flag name the package had dropped.
    # Comparison is per column: a float survives the round trip only to about
    # its last digit, and an empty string comes back as NaN.
    published = pd.read_csv(DATA / "tidy.csv")
    assert list(published.columns) == list(tidy.columns)
    assert len(published) == len(tidy)

    left = published.reset_index(drop=True)
    right = tidy.reset_index(drop=True)
    numbers = pd.testing.assert_series_equal
    numbers(left["value"], right["value"], check_exact=False, rtol=1e-9)
    for column in left.columns.drop("value"):
        a = left[column].fillna("").astype(str)
        b = right[column].fillna("").astype(str)
        differing = (a != b).sum()
        assert not differing, f"{column}: {differing} rows differ; run twstat extract"


def test_no_two_observations_claim_the_same_thing(tidy):
    # Two rows with the same table, section, year and dimensions describe the
    # same quantity, so they cannot hold different numbers. When three health
    # tables were read with one header band each, 726 keys broke this and every
    # value in them was individually correct. It is the cheapest structural
    # check that would have caught it.
    key = ["table_id", "section", "year", "dim1", "dim2"]
    distinct = tidy.dropna(subset=["value"]).groupby(key, dropna=False)["value"].nunique()
    conflicting = distinct[distinct > 1]
    assert conflicting.empty, f"{len(conflicting)} keys carry more than one value"


def test_each_source_cell_is_used_once(tidy):
    counts = tidy.groupby(["table_id", "src_row", "src_col"]).size()
    assert counts.max() == 1


def test_the_committed_notes_are_what_the_package_produces(raw_dir, tmp_path):
    # data/notes.csv is written by `twstat notes raw data/notes.csv`, and until
    # this test nothing compared it with the code. data/tidy.csv drifted in
    # exactly that position.
    from twstat.cli import main

    produced = tmp_path / "notes.csv"
    assert main(["notes", str(raw_dir), str(produced)]) == 0
    assert pd.read_csv(produced).equals(pd.read_csv(DATA / "notes.csv"))
