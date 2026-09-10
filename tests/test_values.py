"""Cell interpretation, including the source's own missing-value legend."""

import pytest

from twstat.values import Flag, parse


@pytest.mark.parametrize(
    "cell, number", [("69", 69.0), ("1,234", 1234.0), ("10 079", 10079.0), (5, 5.0)]
)
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


def test_a_value_is_falsy_when_no_number_was_read():
    assert not parse("－")
    assert parse("1,234")


# A figure spanning several printed columns is set inside a drawn brace, and the
# digitisation kept the brace. The brace is drawn to whatever width the printer
# needed, so its spelling varies. Every string below is taken verbatim from the
# corpus; see docs/W06_layout.md.


@pytest.mark.parametrize(
    "cell, number",
    [
        ("└─42─┘", 42.0),
        ("┌─1─┐", 1.0),
        ("└──126──┘", 126.0),
        ("┌────298────┐", 298.0),
        ("└───────76───────┘", 76.0),
        ("└────────────────────385────────────────────┘", 385.0),
        ("┐4.61", 4.61),
        ("├5421.4627", 5421.4627),
        ("└─67435496─┘", 67435496.0),
    ],
)
def test_braced_figures_are_read_whatever_the_brace_looks_like(cell, number):
    parsed = parse(cell)
    assert parsed.number == number
    assert parsed.flag is Flag.BRACKET_ARTIFACT


def test_a_braced_missing_marker_stays_missing():
    # The compilers' dot can be braced too. It still means not surveyed, and
    # reading it as unreadable would drop the row from the tidy output.
    parsed = parse("└─.─┘")
    assert parsed.number is None
    assert parsed.flag is Flag.MISSING


@pytest.mark.parametrize("cell", ["└32.12.22", "181─365日", "+", "│"])
def test_typography_that_is_not_a_figure_is_not_read_as_one(cell):
    # └32.12.22 is a date, 181─365日 a range of days, and + and │ are the
    # printed operator and rule of a table whose columns were kept as data.
    parsed = parse(cell)
    assert parsed.number is None
    assert parsed.flag is Flag.NON_NUMERIC
