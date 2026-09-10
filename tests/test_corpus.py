"""Checks against the real corpus. Skipped when the source files are absent."""

import pytest

from twstat import extract_corpus, verify
from twstat.corpus1946 import build

pytestmark = pytest.mark.corpus


@pytest.fixture(scope="module")
def tidy(raw_dir):
    return extract_corpus(raw_dir, build())


def test_expected_shape(tidy):
    # 36,570 until the brace pattern was widened in docs/W06_layout.md, which
    # recovered 102 figures that had been set inside a drawn brace and were
    # being discarded as unreadable. No existing value changed.
    assert len(tidy) == 36_672
    assert tidy["table_id"].nunique() == 48
    assert tidy.groupby(["table_id", "section"]).ngroups == 65


def test_every_value_matches_its_source_cell(tidy, raw_dir):
    assert verify(tidy, raw_dir) == []


def test_years_lie_inside_the_colonial_period(tidy):
    assert tidy["year"].min() == 1897
    assert tidy["year"].max() == 1945


def test_no_fragmented_labels_survive(tidy):
    # A single-character dimension means a scattered header was not reassembled.
    assert not [label for label in tidy["dim1"].dropna().unique() if len(label) <= 1]


def test_period_types_are_all_recognised(tidy):
    assert not tidy["period_type"].isna().any()


def test_specification_covers_every_downloaded_file(raw_dir):
    book = build()
    stems = {path.stem for path in raw_dir.glob("*.xls")}
    # Two files are cross-sectional and deliberately excluded.
    assert stems - book.files() == {"Edu_Mt467", "Hygiene_Mt496"}
