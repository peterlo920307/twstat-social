"""Cell interpretation, including the source's own missing-value legend."""

import pytest

from twstat.values import Flag, parse


@pytest.mark.parametrize("cell, number", [("69", 69.0), ("1,234", 1234.0), ("10 079", 10079.0), (5, 5.0)])
def test_numbers(cell, number):
    parsed = parse(cell)
    assert parsed.number == number
    assert parsed.flag is None


@pytest.mark.parametrize("cell", [".", "．", "…", "-", "－", "─", "", None, "nan"])
def test_missing_markers(cell):
    parsed = parse(cell)
    assert parsed.number is None
    assert parsed.flag is Flag.MISSING


def test_zero_is_not_zero():
    # Clause 11 of the compilation notes: "0" means a quantity below one unit.
    parsed = parse("0")
    assert parsed.flag is Flag.LESS_THAN_ONE_UNIT
    assert parsed.number == 0.0


def test_bracket_artifact_yields_its_value():
    parsed = parse("└─42─┘")
    assert parsed.number == 42.0
    assert parsed.flag is Flag.BRACKET_ARTIFACT


def test_text_is_flagged_not_silently_dropped():
    parsed = parse("見附註")
    assert parsed.number is None
    assert parsed.flag is Flag.NON_NUMERIC


def test_missing_is_distinguishable_from_below_one_unit():
    # Filling either with zero would be wrong, but for different reasons.
    assert parse(".").flag is not parse("0").flag
