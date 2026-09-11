"""Run the layout code over the chapters of the compendium it has never seen.

The published dataset uses 50 tables from three chapters. The compendium has 24
chapters and 634 tables. The rest are the same typesetting conventions applied by
the same compilers to subjects nobody here has looked at, which makes them a fair
test of whether `sections` and `values` encode the conventions or merely the
fifty tables that were in front of us.

The files are not redistributed. This script downloads them into a directory of
your choosing and prints the measurements quoted in docs/W06_layout.md.

    python scripts/holdout.py /path/to/scratch
"""

import collections
import json
import os
import re
import sys
import time
import urllib.parse

import _fetch  # scripts/_fetch.py
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# Use this checkout's package even before `pip install -e .` has been run.
sys.path.insert(0, os.path.join(ROOT, "src"))

# This script also reads the private sections._MARKER; renaming it breaks this.
from twstat import sections as sectioning  # noqa: E402
from twstat import values  # noqa: E402

# The address the server redirects every older form of the URL to. The host
# does not care about case: EDU/Mt468.xls is answered from EDU/MT468.XLS.
BASE = "https://twstudy.iis.sinica.edu.tw/TwStatistic50/"
PUBLISHED = {"Edu", "Hygiene", "Welfare"}
INDEX = os.path.join(ROOT, "docs", "twstat50_tables.json")

# Seconds between requests. Half the pause of download_raw.py, because there
# are twelve times as many files: 599 of them take about five minutes of waiting,
# which is still a load a small academic server will not notice.
PAUSE = 0.5

# A marker written with either full stop, which is what the detector should see.
MARKER = re.compile(r"^[0-9０-９]+[.．]\s*[^\d０-９]")
BRACE_CHARS = "┌└├┐┘┤│─—"


def unpublished():
    """Return the index entries of the 21 chapters the dataset does not use."""
    with open(INDEX, encoding="utf-8") as handle:
        tables = json.load(handle)
    return {chapter: items for chapter, items in tables.items() if chapter not in PUBLISHED}


def refuse_published(out):
    """Stop if ``out`` holds files from the three published chapters.

    That means ``raw/`` was given by mistake. Measuring it would mix the tables
    the code was written against into the test of whether it generalises.

    Raises:
        SystemExit: ``out`` contains an ``Edu_``, ``Hygiene_`` or ``Welfare_`` file.
    """
    if not os.path.isdir(out):
        return
    try:
        names = os.listdir(out)
    except OSError as error:
        raise SystemExit(f"cannot read {out}: {error}") from error
    prefixes = tuple(f"{chapter}_" for chapter in sorted(PUBLISHED))
    found = sorted(name for name in names if name.startswith(prefixes))
    if found:
        raise SystemExit(
            f"{out} already holds {len(found)} files from the published chapters"
            f" ({found[0]}, ...). It looks like raw/; give holdout.py a directory of its own."
        )


def download(out):
    """Fetch every table of the 21 unpublished chapters into ``out``.

    Returns:
        The number of files that could not be fetched.
    """
    totals = collections.Counter()
    for chapter, items in sorted(unpublished().items()):
        counts = collections.Counter()
        for table in items:
            name = f"{chapter}_{os.path.basename(table['file'])}"
            dest = os.path.join(out, name)
            if _fetch.looks_complete(dest):
                counts["present"] += 1
                continue
            if os.path.exists(dest):
                # Left by an earlier version of this script, which wrote
                # whatever the server sent straight to the final name.
                print(f"  {name} is incomplete or not a spreadsheet; fetching it again")
            url = BASE + urllib.parse.quote(table["file"])
            try:
                _fetch.download(url, dest, timeout=120)
                counts["fetched"] += 1
            except _fetch.FetchError as error:
                counts["failed"] += 1
                print(f"  failed {name}: {error}")
            time.sleep(PAUSE)
        print(
            f"  {chapter}: fetched {counts['fetched']}, present {counts['present']},"
            f" failed {counts['failed']}",
            flush=True,
        )
        totals.update(counts)
    print(
        f"  all chapters: fetched {totals['fetched']}, present {totals['present']},"
        f" failed {totals['failed']}"
    )
    return totals["failed"]


def measure(out):
    """Report what section detection and cell interpretation make of the files.

    Returns:
        The number of files that could be read.
    """
    # Case-insensitively: 17 of the 599 tables are named .XLS, and a
    # case-sensitive filter dropped them from every measurement while the
    # download reported success.
    paths = sorted(
        os.path.join(out, name)
        for name in os.listdir(out)
        if name.lower().endswith((".xls", ".xlsx"))
    )
    per_file = collections.Counter()
    flags = collections.Counter()
    furniture = collections.Counter()
    missed_markers = collections.Counter()
    cross_sectional = 0
    sections_seen = 0
    cells = 0
    unreadable = 0

    for path in paths:
        try:
            frame = pd.read_excel(path, header=None)
        except Exception as error:
            unreadable += 1
            print(f"  unreadable {os.path.basename(path)}: {type(error).__name__}: {error}")
            continue
        if frame.empty:
            continue

        found = sectioning.find(frame)
        per_file[len(found)] += 1
        for section in found:
            sections_seen += 1
            first, _ = sectioning.header_rows(frame, section)
            if first is None:
                cross_sectional += 1

        for row in range(len(frame)):
            for column in range(min(5, frame.shape[1])):
                text = sectioning.clean(frame.iat[row, column])
                looks_like_a_marker = text and len(text) < 40 and MARKER.match(text)
                if looks_like_a_marker and not sectioning._MARKER.match(text):
                    missed_markers[text] += 1
            for column in range(1, frame.shape[1]):
                text = sectioning.clean(frame.iat[row, column])
                if not text:
                    continue
                cells += 1
                value = values.parse(text)
                flags[value.flag.value if value.flag else "(number)"] += 1
                if value.number is None and set(text) <= set(BRACE_CHARS + "+"):
                    furniture[text] += 1

    print(f"\nfiles                            {len(paths) - unreadable}")
    if unreadable:
        print(f"  left out as unreadable         {unreadable}")
    print("sections detected per file:")
    for count in sorted(per_file):
        print(f"  {count:3d} sections   {per_file[count]:4d} files")
    print(f"sections in total                {sections_seen}")
    print(
        f"  of those, cross-sectional      {cross_sectional}"
        f"  ({cross_sectional / max(1, sections_seen):.1%})"
    )
    print(f"markers the detector still misses {sum(missed_markers.values())}")
    for text, count in missed_markers.most_common(10):
        print(f"     {count:4d}  {text!r}")
    print(f"\nnon-blank cells right of column 1 {cells}")
    for flag, count in flags.most_common():
        print(f"  {count:8d}  {count / max(1, cells):6.1%}  {flag}")
    print("printed furniture kept as cells:")
    for text, count in furniture.most_common(8):
        print(f"     {count:5d}  {text!r}")
    return len(paths) - unreadable


def main():
    """Download the unpublished chapters and measure them.

    Returns:
        0 if every table was fetched and measured, otherwise 1.
    """
    _fetch.utf8_console()
    out = sys.argv[1] if len(sys.argv) > 1 else "holdout"
    refuse_published(out)
    _fetch.require_writable(out)
    failed = download(out)
    if failed:
        print(f"({failed} files could not be fetched; the measurements below omit them)")
    measured = measure(out)
    expected = sum(len(items) for items in unpublished().values())
    if measured != expected:
        sys.stdout.flush()
        print(
            f"\nwarning: measured {measured} files, but docs/twstat50_tables.json lists"
            f" {expected} tables in the unpublished chapters. The figures above will"
            " not match docs/W06_layout.md.",
            file=sys.stderr,
        )
    return 1 if failed or measured != expected else 0


if __name__ == "__main__":
    raise SystemExit(main())
