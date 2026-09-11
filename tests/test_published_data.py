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
    assert len(below) == 1
    assert (below["value"] == 0.0).all()


def test_table_491_zeros_are_exact(tidy):
    # Its own footnote overrides clause 11: a 0 there means cases and no deaths.
    zeros = tidy[(tidy["table_id"] == "Mt491") & (tidy["value"] == 0.0)]
    assert len(zeros) == 46
    assert zeros["flag"].isna().all()


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


def test_the_full_precision_values_are_the_documented_ratio_columns(tidy):
    # The printed book gives at most two decimal places. Values with more were
    # computed in the 2006 spreadsheet, and CODEBOOK section 2a-2 lists them as
    # 21 ratio columns in three tables. A new one appearing means a column has
    # changed character and the codebook needs revisiting.
    def places(value: float) -> int:
        text = repr(float(value))
        return len(text.split(".")[1]) if "." in text and "e" not in text else 0

    values = tidy.dropna(subset=["value"])
    long = values[values["value"].map(places) > 4]
    assert set(long["table_id"]) == {"Mt480", "Mt481", "Mt482"}
    assert long.groupby(["table_id", "src_col"]).ngroups == 21


ROOT = DATA.parent


def test_the_readme_headline_is_the_data(tidy):
    # These figures have gone stale in the prose four times, each time a reading
    # rule changed and the data moved without the sentence that describes it.
    import re

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    found = re.search(
        r"\*\*([\d,]+) rows, ([\d,]+) values, (\d+) tables,\s*(\d{4})–(\d{4})", readme
    )
    assert found, "README no longer states its headline figures in the expected form"
    rows, values, tables, first, last = found.groups()
    assert int(rows.replace(",", "")) == len(tidy)
    assert int(values.replace(",", "")) == int(tidy["value"].notna().sum())
    assert int(tables) == tidy["table_id"].nunique()
    assert (int(first), int(last)) == (tidy["year"].min(), tidy["year"].max())


def test_the_codebook_table_list_is_the_data(tidy):
    import re

    codebook = (ROOT / "docs" / "CODEBOOK.md").read_text(encoding="utf-8")
    listed = re.findall(r"^\| (Mt[\d-]+) \| .*? \| \d+×\d+ \| (.*?) \| (\d+) \|$", codebook, re.M)
    assert len(listed) == 50
    for table_id, span, count in listed:
        years = tidy.loc[tidy["table_id"] == table_id, "year"].unique()
        if span == "橫斷面":
            assert len(years) == 0, table_id
            continue
        assert span == f"{years.min()}–{years.max()}", table_id
        assert int(count) == len(years), table_id


def test_the_codebook_flag_counts_are_the_data(tidy):
    import re

    codebook = (ROOT / "docs" / "CODEBOOK.md").read_text(encoding="utf-8")
    counts = dict(re.findall(r"^\| `(\w+)` \| .*\| ([\d,]+) \|$", codebook, re.M))
    blank = re.search(r"^\| （空） \| 數字 \| 一般數值 \| ([\d,]+) \|$", codebook, re.M)
    actual = tidy["flag"].value_counts()
    for flag in ("missing", "less_than_one_unit", "bracket_artifact"):
        assert int(counts[flag].replace(",", "")) == actual.get(flag, 0), flag
    assert blank and int(blank.group(1).replace(",", "")) == int(tidy["flag"].isna().sum())
