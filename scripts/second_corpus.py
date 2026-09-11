"""Test the era-date parser against corpora it was not written against.

Two independent sources are used, both published by the Institute of Economic
Research, Hitotsubashi University, and both freely downloadable:

  LTES      Estimates of Long-Term Economic Statistics of Japan since 1868.
            A modern re-publication that has already normalised its dates.
  Yearbook  The contents index to the Japanese Imperial Statistical Yearbook,
            1882-1940. Table titles carry era dates as they were printed, and
            each row also gives the Gregorian year, which makes the file a
            labelled test set.

Neither is redistributed here. Run this script to fetch them into a directory of
your choosing and print the measurements quoted in docs/W05_generalisation.md.

    python scripts/second_corpus.py /path/to/scratch
"""

import collections
import os
import re
import sys
import urllib.parse

import _fetch  # scripts/_fetch.py
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
# Use this checkout's package even before `pip install -e .` has been run.
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

# This script also reads the private sections._MARKER; renaming it breaks this.
from twstat import eradate  # noqa: E402
from twstat import sections as sectioning  # noqa: E402

LTES_INDEX = "https://d-infra.ier.hit-u.ac.jp/Japanese/ltes/a000.html"
YEARBOOK = "https://d-infra.ier.hit-u.ac.jp/Japanese/govstat-database/statistical-yb/"
YEARBOOK_FILES = ["contents_1882-1911.xlsx", "contents_1912-1940_20210212.xlsx"]

# Volumes 1 to 5 of LTES, in eight workbooks: LTES_01_20221028.xlsx, and
# LTES_03_01_20230107.xlsx for the first part of volume 3. The index page lists
# other volumes and other workbooks as well, so the files are picked by name
# rather than by their position on the page. The date is the issue; the
# figures in docs/W05_generalisation.md come from issues dated October 2022 to
# March 2023, and the script prints the names it used.
LTES_FILE = re.compile(r"LTES_0[1-5](_0[1-9])?_\d{8}\.xlsx")
LTES_WORKBOOKS = 8

ERA_NAME = re.compile(r"(明治|大正|昭和|平成|令和|民國前|民國|民国)")
ERA_EXPR = re.compile(r"(明治|大正|昭和)\s*[0-9０-９一二三四五六七八九十元]+\s*年[度末]*")
ERA_STARTS = {"明治": 1867, "大正": 1911, "昭和": 1925}


class MeasurementError(Exception):
    """A corpus is not in the shape the measurements need."""


def fetch(url, dest):
    """Download ``url`` to ``dest`` unless a complete copy is already there."""
    if not _fetch.looks_complete(dest):
        _fetch.download(url, dest, timeout=180)
    return dest


def read(url):
    """Download ``url`` and decode it as text."""
    return _fetch.get(url, timeout=90).payload.decode("utf-8", "replace")


def read_excel(path):
    """Read the first sheet of a workbook, naming the file if that fails.

    Raises:
        MeasurementError: The file could not be read.
    """
    try:
        return pd.read_excel(path, header=None)
    except Exception as error:
        raise MeasurementError(f"cannot read {path}: {type(error).__name__}: {error}") from error


def sheets(path):
    """Yield every sheet of a workbook as an unheadered frame.

    Raises:
        MeasurementError: The file could not be read.
    """
    try:
        with pd.ExcelFile(path) as book:
            for name in book.sheet_names:
                yield name, book.parse(name, header=None)
    except Exception as error:
        raise MeasurementError(f"cannot read {path}: {type(error).__name__}: {error}") from error


def check_ltes(out):
    """Report how many LTES labels carry an era name.

    Raises:
        MeasurementError: The index page does not list exactly eight workbooks
            for volumes 1 to 5.
    """
    links = re.findall(r'href="([^"]+\.xlsx?)"', read(LTES_INDEX))
    urls = sorted(
        {
            urllib.parse.urljoin(LTES_INDEX, link)
            for link in links
            if LTES_FILE.fullmatch(os.path.basename(link))
        }
    )
    if len(urls) != LTES_WORKBOOKS:
        found = ", ".join(os.path.basename(url) for url in urls) or "none"
        raise MeasurementError(
            f"expected {LTES_WORKBOOKS} workbooks for LTES volumes 1-5 on {LTES_INDEX},"
            f" found {len(urls)}: {found}. The page has changed; the figures in"
            " docs/W05_generalisation.md cannot be reproduced from it as it stands."
        )
    paths = [fetch(url, os.path.join(out, os.path.basename(url))) for url in urls]

    labels, era_labels, sheet_count = collections.Counter(), collections.Counter(), 0
    for path in paths:
        for _, frame in sheets(path):
            sheet_count += 1
            for column in range(min(3, frame.shape[1])):
                for cell in frame.iloc[:, column].dropna():
                    text = str(cell).strip()
                    if text and len(text) <= 30:
                        labels[text] += 1
                        if ERA_NAME.search(text):
                            era_labels[text] += 1
    print("LTES")
    print(f"  workbooks {', '.join(os.path.basename(path) for path in paths)}")
    print(f"  volumes {len(paths)}, sheets {sheet_count}")
    print(f"  distinct short labels          {len(labels)}")
    print(f"  labels naming an era           {sum(era_labels.values())}")
    print("  (a modern re-publication: the dates were normalised by its editors,")
    print("   and the fiscal-year distinction survives only in prose footnotes)")


def check_yearbook(out):
    """Report what the parser makes of the yearbook index.

    The file gives the Gregorian year alongside the era year, so it also serves
    as a labelled test of the arithmetic conversion this package declines to do.
    """
    frames = []
    for name in YEARBOOK_FILES:
        path = fetch(YEARBOOK + name, os.path.join(out, name))
        for _, frame in sheets(path):
            frame.columns = list(frame.iloc[0])
            frames.append(frame.iloc[1:])
    table = pd.concat(frames, ignore_index=True)

    titles = [str(v).strip() for v in table["統計表タイトル"].dropna() if str(v).strip()]
    periods, resolved = collections.Counter(), 0
    for title in titles:
        date = eradate.parse(title)
        periods[date.period.value if date.period else "(none)"] += 1
        resolved += date.year is not None

    expressions = collections.Counter()
    for title in titles:
        for match in ERA_EXPR.finditer(title):
            expressions[match.group(0)] += 1
    expr_periods, expr_resolved = collections.Counter(), 0
    for expression, count in expressions.items():
        date = eradate.parse(expression)
        expr_periods[date.period.value if date.period else "(none)"] += count
        if date.year is not None:
            expr_resolved += count

    pairs = {}
    for era, gregorian in zip(table["和暦"], table["西暦"], strict=True):
        if pd.isna(era) or pd.isna(gregorian):
            continue
        pairs.setdefault(str(era).strip(), set()).add(int(gregorian))
    agree = disagree = 0
    for era, years in pairs.items():
        guessed = arithmetic(era)
        if guessed is None:
            continue
        agree, disagree = (agree + 1, disagree) if guessed in years else (agree, disagree + 1)

    print("\nImperial Statistical Yearbook index, 1882-1940")
    print(f"  table titles                   {len(titles)}")
    print(f"  period type recognised         {len(titles) - periods['(none)']}")
    for key, count in periods.most_common():
        print(f"     {count:7d}  {key}")
    print(f"  Gregorian year resolved        {resolved}")
    print(
        f"  embedded era expressions       {sum(expressions.values())}"
        f" ({len(expressions)} distinct)"
    )
    for key, count in expr_periods.most_common():
        print(f"     {count:7d}  {key}")
    print(f"  of those, year resolved        {expr_resolved}")
    print(f"  labelled era/Gregorian pairs   {len(pairs)}")
    print(f"  arithmetic conversion agrees   {agree}, disagrees {disagree}")


def arithmetic(text):
    """Convert a Japanese era year to a Gregorian year, or return ``None``."""
    match = re.match(r"(明治|大正|昭和)\s*([0-9０-９]+|元)", text)
    if not match:
        return None
    digits = match.group(2)
    number = (
        1
        if digits == "元"
        else int(digits.translate(str.maketrans("０１２３４５６７８９", "0123456789")))
    )
    return ERA_STARTS[match.group(1)] + number


CHINESE = {
    "元": 1,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}
OWN_ERA = re.compile(r"(民國前|民國)\s*([元一二三四五六七八九十 ]+?)\s*年")
OWN_GREGORIAN = re.compile(r"[(（]\s*(1[89]\d\d)\s*[)）]")


def chinese_numeral(text):
    """Read a Chinese numeral up to 99, or return ``None``."""
    text = text.replace(" ", "")
    if not text or any(character not in CHINESE for character in text):
        return None
    if "十" not in text:
        return CHINESE[text] if len(text) == 1 else None
    tens, _, units = text.partition("十")
    return (CHINESE[tens] if tens else 1) * 10 + (CHINESE[units] if units else 0)


def check_own_corpus(raw):
    """Measure the claims the eradate docstring makes about the 1946 corpus.

    Raises:
        MeasurementError: ``raw`` has no date-like row labels to measure, or a
            file in it cannot be read.
    """
    if not os.path.isdir(raw):
        print(f"\n(skipping the 1946 corpus: {raw} is absent)")
        return
    japanese = re.compile(r"(明治|大正|昭和)")
    cells = japanese_hits = 0
    labels = collections.Counter()
    for name in sorted(os.listdir(raw)):
        if not name.lower().endswith((".xls", ".xlsx")):
            continue
        frame = read_excel(os.path.join(raw, name))
        for row in range(len(frame)):
            for column in range(frame.shape[1]):
                text = sectioning.clean(frame.iat[row, column])
                if not text:
                    continue
                cells += 1
                japanese_hits += bool(japanese.search(text))
            first = sectioning.clean(frame.iat[row, 0])
            if first and not eradate.is_note(first) and not sectioning._MARKER.match(first):
                labels[first] += 1

    # A date-like label is short and carries a period marker. Longer strings are
    # table titles and footnote text, which are not dated rows.
    datelike = {k: v for k, v in labels.items() if len(k) <= 24 and eradate.parse(k).period}
    total = sum(datelike.values())
    if not total:
        raise MeasurementError(
            f"{raw} has no date-like row labels ({cells} non-blank cells in all);"
            " it should be the raw/ that scripts/download_raw.py fills"
        )
    named = sum(v for k, v in datelike.items() if ERA_NAME.search(k))
    printed = sum(v for k, v in datelike.items() if OWN_GREGORIAN.search(k))

    agree = disagree = 0
    for label, count in labels.items():
        era, gregorian = OWN_ERA.search(label), OWN_GREGORIAN.search(label)
        if not (era and gregorian):
            continue
        number = chinese_numeral(era.group(2))
        if number is None:
            continue
        guessed = 1912 - number if era.group(1) == "民國前" else 1911 + number
        agree, disagree = (
            (agree + count, disagree)
            if guessed == int(gregorian.group(1))
            else (agree, disagree + count)
        )

    print("\nThe 1946 compendium, for comparison")
    print(f"  non-blank cells                {cells}")
    print(f"  cells naming a Japanese era    {japanese_hits}")
    print(f"  date-like row labels           {total} ({len(datelike)} distinct)")
    print(f"  carrying a printed year        {printed} ({printed / total:.1%})")
    print(f"  naming an era                  {named} ({named / total:.1%})")
    print(f"  arithmetic conversion agrees   {agree}, disagrees {disagree}")


def main():
    """Fetch both corpora and print the measurements.

    Each of the three measurements runs even if another fails.

    Returns:
        0 if all three could be made, otherwise 1.
    """
    _fetch.utf8_console()
    out = sys.argv[1] if len(sys.argv) > 1 else "second_corpus"
    raw = sys.argv[2] if len(sys.argv) > 2 else "raw"
    _fetch.require_writable(out)
    failed = 0
    for check, argument in ((check_ltes, out), (check_yearbook, out), (check_own_corpus, raw)):
        try:
            check(argument)
        except (_fetch.FetchError, MeasurementError) as error:
            failed += 1
            sys.stdout.flush()
            print(f"\n{check.__name__} failed: {error}", file=sys.stderr, flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
