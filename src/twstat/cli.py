"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface. Returns a process exit code."""
    parser = argparse.ArgumentParser(
        prog="twstat",
        description="Recover tidy data from legacy East Asian statistical tables.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("extract", help="extract the 1946 compendium into tidy rows")
    build.add_argument("raw", type=Path, help="directory holding the source .xls files")
    build.add_argument("output", type=Path, help="destination CSV")

    check = sub.add_parser("verify", help="check every value against its source cell")
    check.add_argument("tidy", type=Path, help="the extracted CSV")
    check.add_argument("raw", type=Path, help="directory holding the source .xls files")

    notes = sub.add_parser("notes", help="extract the compilers' footnotes")
    notes.add_argument("raw", type=Path)
    notes.add_argument("output", type=Path)
    notes.add_argument(
        "--items",
        type=Path,
        help="also write each note's numbered items, the table a label's (1) resolves against",
    )

    sample = sub.add_parser("sample", help="draw a blank coding sheet for a human coder")
    sample.add_argument("tidy", type=Path, help="the extracted CSV")
    sample.add_argument("output", type=Path, help="destination CSV")
    sample.add_argument(
        "--size",
        type=int,
        default=200,
        help="rows to draw before stratification trims (default 200)",
    )
    sample.add_argument("--seed", type=int, default=20260909, help="random seed")

    args = parser.parse_args(argv)

    import pandas as pd

    from .corpus1946 import build as build_specs
    from .extract import SPREADSHEET_SUFFIXES, extract_corpus
    from .notes import extract_notes, note_items
    from .sampling import coding_sheet
    from .verify import verify

    if args.command == "extract":
        frame = extract_corpus(args.raw, build_specs())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(
            f"{args.output}: {len(frame):,} rows, "
            f"{frame['value'].notna().sum():,} values, "
            f"{frame['table_id'].nunique()} tables"
        )
        return 0

    if args.command == "verify":
        frame = pd.read_csv(args.tidy)
        mismatches = verify(frame, args.raw)
        checked = frame["value"].notna().sum()
        if mismatches:
            for item in mismatches[:20]:
                print(f"{item.table_id} r{item.src_row} c{item.src_col}: {item.reason}")
            plural = "" if len(mismatches) == 1 else "es"
            print(f"{len(mismatches)} mismatch{plural} out of {checked:,}", file=sys.stderr)
            return 1
        print(f"{checked:,} values checked, no mismatches")
        return 0

    if args.command == "sample":
        sheet = coding_sheet(pd.read_csv(args.tidy), size=args.size, seed=args.seed)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sheet.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(
            f"{args.output}: {len(sheet)} rows across "
            f"{sheet.groupby(['table_id', 'section']).ngroups} sections, seed {args.seed}"
        )
        return 0

    # Both suffixes, for the third time. The same narrowing was fixed in verify
    # and then in extract_corpus, and it survived here because no test called
    # this command with a directory of .xlsx files.
    paths = sorted(
        path for suffix in SPREADSHEET_SUFFIXES for path in Path(args.raw).glob(f"*{suffix}")
    )
    rows = [note for path in paths for note in extract_notes(path)]
    pd.DataFrame(rows).to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"{args.output}: {len(rows)} notes from {len({r.file for r in rows})} files")
    if args.items:
        items = note_items(pd.read_csv(args.output))
        items.to_csv(args.items, index=False, encoding="utf-8-sig")
        print(f"{args.items}: {len(items)} numbered items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
