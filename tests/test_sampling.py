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


def test_coding_sheet_trims_to_the_requested_size(tidy):
    # Three groups always contribute at least one row each, so a size of two
    # is over-filled and then trimmed back to what was asked for.
    sheet = coding_sheet(tidy, size=2, seed=0)
    assert len(sheet) == 2


def test_kappa_rejects_an_empty_comparison():
    with pytest.raises(ValueError):
        cohen_kappa([], [])


def test_kappa_is_one_when_both_coders_used_a_single_label():
    # Chance agreement is 1.0 here, so the usual formula divides by zero. Two
    # coders who only ever wrote the same label agree completely by
    # construction; there is no information to correct for.
    assert cohen_kappa(list("aaa"), list("aaa")) == 1.0


def test_kappa_is_zero_when_a_single_label_still_disagrees():
    # Both coders used one label each but not the same one. Expected agreement
    # is still 1.0, and observed agreement is 0.
    assert cohen_kappa(list("aaa"), list("bbb")) == 0.0


def _cells(table_id, section, rows, dim1="甲"):
    # One entry per cell of a rows-by-three grid, the shape a real section has.
    return [
        {
            "table_id": table_id,
            "section": section,
            "year": 1900 + row,
            "src_row": row,
            "src_col": col,
            "value": float(row * 10 + col),
            "dim1": dim1,
        }
        for row in range(1, rows + 1)
        for col in (2, 3, 4)
    ]


def test_a_large_section_does_not_crowd_out_small_ones():
    # A simple random draw of eight rows from this would be almost all Mt1.
    # The point of stratifying is that a two-row section of a small table gets
    # checked as often as a section with three hundred rows.
    tidy = pd.DataFrame(
        _cells("Mt1", 1, 100) + _cells("Mt2", 1, 2) + _cells("Mt3", 1, 2) + _cells("Mt3", 2, 2)
    )
    sheet = coding_sheet(tidy, size=8)
    counts = sheet.groupby(["table_id", "section"]).size().to_dict()
    assert counts == {("Mt1", 1): 2, ("Mt2", 1): 2, ("Mt3", 1): 2, ("Mt3", 2): 2}


def test_the_sheet_is_in_source_order():
    # A coder works down each file in turn. Mt1's only section is numbered 2
    # and Mt2's is numbered 1, and each is a grid, so sorting by any other key
    # order, or not at all, gives a different sequence.
    tidy = pd.DataFrame(_cells("Mt2", 1, 5) + _cells("Mt1", 2, 5))
    sheet = coding_sheet(tidy, size=30)
    keys = list(
        zip(sheet["table_id"], sheet["section"], sheet["src_row"], sheet["src_col"], strict=True)
    )
    assert len(keys) == 30
    assert keys == sorted(keys)
    assert list(sheet.index) == list(range(30))


def test_rows_without_a_dim1_never_reach_a_coder():
    # A row with no dim1 has no pipeline answer to compare the coder's with,
    # so a coder's time on it is wasted. Mt1 section 2 has none at all and must
    # not appear; in Mt2 only the rows that have a dim1 may be drawn.
    tidy = pd.DataFrame(
        _cells("Mt1", 1, 2)
        + _cells("Mt1", 2, 2, dim1=None)
        + _cells("Mt2", 1, 1, dim1=None)
        + _cells("Mt2", 1, 2, dim1="乙")[3:]
    )
    sheet = coding_sheet(tidy, size=100)
    labelled = tidy[tidy["dim1"].notna()]
    key = ["table_id", "section", "src_row", "src_col"]
    assert sheet[key].values.tolist() == labelled[key].values.tolist()
