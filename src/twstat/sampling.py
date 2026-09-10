"""Sampling for human checking, and agreement between coders.

Verification splits into two questions that need different methods. Whether a
number was read correctly can be checked completely and mechanically against the
source cell, so it needs no sampling at all. What a column *means* cannot: the
label characters are distributed across the columns they span, and a plausible
reconstruction can be wrong in ways no automated check detects. That question
needs people, and people need to be checked against each other.

This module supports the second question only.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

import pandas as pd

__all__ = ["coding_sheet", "cohen_kappa"]


def coding_sheet(
    tidy: pd.DataFrame,
    size: int = 200,
    seed: int = 20260909,
) -> pd.DataFrame:
    """Draw a sheet for a coder to fill in, stratified across sections.

    The coder is given the source coordinates and the value, and writes what the
    column means. The pipeline's own answer is deliberately absent, so that the
    coding is independent of it.
    """
    populated = tidy[tidy["dim1"].notna()]
    groups = populated.groupby(["table_id", "section"], sort=True)
    per_group = max(1, size // max(1, groups.ngroups))

    sample = groups.apply(
        lambda group: group.sample(min(len(group), per_group), random_state=seed),
        include_groups=False,
    ).reset_index()
    if len(sample) > size:
        sample = sample.sample(size, random_state=seed)

    sheet = sample[["table_id", "section", "year", "src_row", "src_col", "value"]].copy()
    sheet["coded_dim1"] = ""
    sheet["coded_dim2"] = ""
    sheet["note"] = ""
    return sheet.sort_values(["table_id", "section", "src_row", "src_col"]).reset_index(drop=True)


def cohen_kappa(first: Sequence[str], second: Sequence[str]) -> float:
    """Agreement between two coders, corrected for chance.

    >>> round(cohen_kappa(["a", "b", "a"], ["a", "b", "a"]), 3)
    1.0
    >>> cohen_kappa(["a", "a"], ["b", "b"])
    0.0
    """
    if len(first) != len(second):
        raise ValueError("coders must have judged the same items")
    if not first:
        raise ValueError("no items to compare")

    total = len(first)
    observed = sum(a == b for a, b in zip(first, second)) / total
    left, right = Counter(first), Counter(second)
    expected = sum(
        (left[label] / total) * (right[label] / total) for label in set(left) | set(right)
    )
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return (observed - expected) / (1 - expected)
