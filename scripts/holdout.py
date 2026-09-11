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
import urllib.request

import pandas as pd

from twstat import sections as sectioning
from twstat import values

BASE = "http://twstudy.iis.sinica.edu.tw/twstatistic50/"
PUBLISHED = {"Edu", "Hygiene", "Welfare"}
HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(os.path.dirname(HERE), "docs", "twstat50_tables.json")

# A marker written with either full stop, which is what the detector should see.
MARKER = re.compile(r"^[0-9０-９]+[.．]\s*[^\d０-９]")
BRACE_CHARS = "┌└├┐┘┤│─—"


def download(out):
    """Fetch every table of the 21 unpublished chapters into ``out``."""
    with open(INDEX, encoding="utf-8") as handle:
        tables = json.load(handle)
    os.makedirs(out, exist_ok=True)
    fetched = present = failed = 0
    for chapter, items in sorted(tables.items()):
        if chapter in PUBLISHED:
            continue
        for table in items:
            dest = os.path.join(out, f"{chapter}_{os.path.basename(table['file'])}")
            if os.path.exists(dest) and os.path.getsize(dest) > 0:
                present += 1
                continue
            url = BASE + urllib.parse.quote(table["file"])
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "twstat-social/0.1"})
                with urllib.request.urlopen(request, timeout=120) as response:
                    payload = response.read()
                with open(dest, "wb") as handle:
                    handle.write(payload)
                fetched += 1
            except Exception as error:
                failed += 1
                print(f"  failed {os.path.basename(dest)}: {str(error)[:60]}")
            time.sleep(0.15)
        print(f"  {chapter}: fetched {fetched}, present {present}, failed {failed}", flush=True)
    return failed


def measure(out):
    """Report what section detection and cell interpretation make of the files."""
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

    for path in paths:
        try:
            frame = pd.read_excel(path, header=None)
        except Exception as error:
            print(f"  unreadable {os.path.basename(path)}: {type(error).__name__}")
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

    print(f"\nfiles                            {len(paths)}")
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


def main():
    """Download the unpublished chapters and measure them."""
    out = sys.argv[1] if len(sys.argv) > 1 else "holdout"
    if download(out):
        print("(some files could not be fetched; the measurements below omit them)")
    measure(out)


if __name__ == "__main__":
    main()
