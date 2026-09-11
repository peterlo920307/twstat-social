"""Checks on the committed data files that do not need the source corpus."""

from pathlib import Path

import pandas as pd
import pytest

from twstat.eradate import Period
from twstat.values import Flag

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def tidy() -> pd.DataFrame:
    return pd.read_csv(DATA / "tidy.csv")


def test_flags_come_from_the_published_vocabulary(tidy):
    used = set(tidy["flag"].dropna().unique())
    assert used <= {flag.value for flag in Flag}


def test_period_types_come_from_the_published_vocabulary(tidy):
    used = set(tidy["period_type"].dropna().unique())
    assert used <= {period.value for period in Period}


def test_a_flagged_zero_is_never_a_plain_zero(tidy):
    # The compilers' printed 0 means a quantity below one unit. It is stored as
    # 0.0, so the flag is the only thing separating it from a true zero.
    below = tidy[tidy["flag"] == Flag.LESS_THAN_ONE_UNIT.value]
    assert len(below) == 47
    assert (below["value"] == 0.0).all()


def test_missing_values_carry_no_number(tidy):
    assert tidy[tidy["flag"] == Flag.MISSING.value]["value"].isna().all()


def test_every_row_names_the_cell_it_came_from(tidy):
    assert tidy["src_row"].notna().all()
    assert tidy["src_col"].notna().all()
    assert (tidy["src_row"] > 0).all()
    assert (tidy["src_col"] > 0).all()


@pytest.fixture(scope="module")
def sheet() -> pd.DataFrame:
    return pd.read_csv(DATA / "validation_sample.csv")


def test_the_coding_sheet_covers_every_section_evenly(sheet):
    assert len(sheet) == 234
    assert sheet["table_id"].nunique() == 48
    counts = sheet.groupby(["table_id", "section"]).size()
    assert counts.nunique() == 1 and counts.iloc[0] == 3


def test_the_coding_sheet_is_blank(sheet):
    # A coder must not be shown an answer to agree with.
    for column in ["coded_dim1", "coded_dim2", "note"]:
        assert sheet[column].isna().all()
    assert "dim1" not in sheet.columns
    assert "dim2" not in sheet.columns


def test_every_row_of_the_coding_sheet_points_at_a_real_observation(sheet, tidy):
    key = ["table_id", "section", "src_row", "src_col"]
    assert sheet.merge(tidy[key], on=key, how="inner").shape[0] == len(sheet)
