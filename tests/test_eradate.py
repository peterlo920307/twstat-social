"""Row-label parsing.

The examples are taken from the source corpus rather than invented, so a change
in behaviour shows up against labels that actually occur.
"""

import pytest

from twstat.eradate import Period, is_note, parse


@pytest.mark.parametrize(
    "label, year, period",
    [
        ("民國前 十 三 年度底(1899)", 1899, Period.FISCAL_YEAR_END),
        ("二十一年底(1932)", 1932, Period.YEAR_END),
        ("十 一 年(1922)", 1922, Period.CALENDAR_YEAR),
        ("二十一年度(1932)", 1932, Period.FISCAL_YEAR),
        ("民國  元    年(1912)", 1912, Period.CALENDAR_YEAR),
        ("十 二 年度底(1900)", 1900, Period.FISCAL_YEAR_END),
        ("三  十年(1941)", 1941, Period.CALENDAR_YEAR),
    ],
)
def test_reads_year_and_period(label, year, period):
    parsed = parse(label)
    assert parsed.year == year
    assert parsed.period is period


def test_period_suffixes_are_tested_longest_first():
    # 年度底 must not be read as 年度 or as 年.
    assert parse("十 年度底(1902)").period is Period.FISCAL_YEAR_END
    assert parse("十 年度(1902)").period is Period.FISCAL_YEAR
    assert parse("十 年底(1902)").period is Period.YEAR_END


def test_academic_year_is_distinguished():
    parsed = parse("民國三十五學年上學期(八月至十月)")
    assert parsed.period is Period.ACADEMIC_YEAR
    assert parsed.year is None  # no Gregorian year printed


@pytest.mark.parametrize(
    "text",
    [
        "附註:(1)國立臺灣大學直隸中央故未列入.",
        "材料來源:根據前臺灣總督府各年統計書材料編製.",
        "註:本表不含高山族",
    ],
)
def test_footnotes_are_not_dates(text):
    assert is_note(text)
    assert parse(text).year is None


@pytest.mark.parametrize("text", ["", "   ", None, "nan", float("nan")])
def test_empty_input_is_handled(text):
    assert parse(text).year is None


def test_years_outside_the_period_are_ignored():
    # A four-digit number that is not a plausible year must not be picked up.
    assert parse("第 2024 表").year is None


def test_raw_is_preserved():
    label = "民國前 十 三 年度底(1899)"
    assert parse(label).raw == label


def test_truthiness_follows_year():
    assert parse("十 一 年(1922)")
    assert not parse("附註:something")


def test_a_blank_cell_is_not_a_note():
    assert is_note(None) is False
