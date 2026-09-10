"""Sampling and inter-coder agreement."""

import pandas as pd
import pytest

from twstat.sampling import coding_sheet, cohen_kappa


@pytest.fixture
def tidy() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "table_id": ["Mt1"] * 6 + ["Mt2"] * 6,
            "section": [1] * 6 + [1] * 3 + [2] * 3,
            "year": list(range(1900, 1906)) * 2,
            "src_row": list(range(1, 7)) * 2,
            "src_col": [2, 3, 4] * 4,
            "value": range(12),
            "dim1": ["甲"] * 12,
        }
    )


def test_sheet_leaves_the_judgement_to_the_coder(tidy):
    sheet = coding_sheet(tidy, size=6)
    assert "dim1" not in sheet.columns
    assert (sheet["coded_dim1"] == "").all()


def test_sheet_keeps_the_source_coordinates(tidy):
    sheet = coding_sheet(tidy, size=6)
    assert {"table_id", "section", "src_row", "src_col"} <= set(sheet.columns)


def test_sheet_spreads_across_sections(tidy):
    sheet = coding_sheet(tidy, size=6)
    assert sheet.groupby(["table_id", "section"]).ngroups == 3


def test_sheet_is_reproducible(tidy):
    assert coding_sheet(tidy, 6, seed=1).equals(coding_sheet(tidy, 6, seed=1))


def test_kappa_is_one_for_perfect_agreement():
    assert cohen_kappa(list("abcab"), list("abcab")) == pytest.approx(1.0)


def test_kappa_is_zero_when_agreement_is_only_chance():
    # Each coder splits evenly and they agree on half the items, which is
    # exactly what independent coding would produce.
    assert cohen_kappa(list("aabb"), list("abab")) == pytest.approx(0.0, abs=1e-9)


def test_kappa_penalises_agreement_below_chance():
    # Observed agreement 0.6 against an expected 0.68 when both coders favour
    # the same label: raw agreement looks high, kappa does not.
    assert cohen_kappa(list("aaaab"), list("aaaba")) == pytest.approx(-0.25)


def test_kappa_is_negative_below_chance():
    assert cohen_kappa(list("aabb"), list("bbaa")) < 0


def test_kappa_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        cohen_kappa(["a"], ["a", "b"])
