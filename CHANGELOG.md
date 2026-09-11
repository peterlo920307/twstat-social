# Changelog

## 0.1.0 — unreleased

First packaged version. The extraction previously lived in a set of loose
scripts; it is now a library with a command line entry point. Output is
identical to those scripts apart from the brace fix below, which recovers 98
figures they were discarding.

### Added
- `twstat.eradate` — era-year and reporting-period parsing.
- `twstat.values` — cell semantics, including the source's own missing-value
  legend, in which a printed `0` means a quantity below one unit.
- `twstat.sections` — detection of several tables stacked in one sheet.
- `twstat.spec` — column specifications, with an explicit distinction between
  "take the innermost header" and "this column has no second dimension".
- `twstat.extract`, `twstat.verify` — extraction, and a complete check of every
  value against the cell it came from.
- `twstat.notes` — recovery of the compilers' footnotes and source attributions.
- `twstat.sampling` — stratified coding sheets and Cohen's kappa.
- `twstat` command: `extract`, `verify`, `notes`, `sample`.

### Fixed
- `verify` compared source cells with a bare `float()` and so reported the
  `└─N─┘` typesetting artifacts as data errors.
- `verify` silently skipped tables whose source file it could not find, and
  could therefore report success for input it had never read. It now raises
  `SourceNotFoundError`.
- `extract_corpus` looked only for `*.xls` and so returned nothing at all,
  without complaint, for a directory of `.xlsx` files. Both suffixes are now
  accepted. This was the same fault already fixed in `verify`; a test written
  for coverage found the second instance of it.
- Section detection accepted only an ASCII period in a marker such as `1.本省人`.
  The compendium uses the full-width U+FF0E interchangeably, and the two are
  indistinguishable in print. 117 markers across 102 of the 599 tables tested in
  `docs/W06_layout.md` went unread, and in 6 of those files two sections were
  merged into one: every figure correct, every attribution wrong. None of the
  affected tables is in the three chapters this package was written against,
  which is why it went unnoticed.
- The pattern for figures set inside a drawn brace matched only `└─N─┘`. The
  same brace is also drawn as `┌─N─┐`, `└──N──┘`, `└───────N───────┘` and with a
  single corner on one side, and those spellings were being discarded as
  unreadable. **98 figures in the published corpus are recovered by this fix**,
  and the file gains 102 rows. No existing value changed. A braced missing marker, `└─.─┘`, is now read as
  missing rather than as unreadable, which keeps its row in the output.

### Changed
- `data/tidy.csv` grows from 36,570 to 36,672 rows, entirely from the brace fix
  above. The committed file has been regenerated; `tests/test_corpus.py` now
  compares it against a fresh extraction, column by column.

### Added, also
- `twstat sample` draws a blank coding sheet from a tidy CSV, stratified across
  sections, for the human check of `dim1` and `dim2` that the numeric
  verification cannot perform.
- `data/validation_sample.csv` — that sheet, 195 cells across all 65 sections,
  committed so a second coder can start without running anything.
- `docs/CODING_SHEET.md` — the instructions for that coder, self-contained.
- `docs/DESIGN.md`, `docs/EXAMPLE.md`, `docs/README.md`,
  `docs/W05_generalisation.md`, `docs/W06_layout.md`.
