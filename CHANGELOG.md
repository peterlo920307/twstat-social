# Changelog

## 0.1.0 — unreleased

First packaged version. The extraction previously lived in a set of loose
scripts; it is now a library with a command line entry point, and produces
output identical to the scripts it replaces.

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
- `twstat` command: `extract`, `verify`, `notes`.

### Fixed
- `verify` compared source cells with a bare `float()` and so reported the
  `└─N─┘` typesetting artifacts as data errors.
- `verify` silently skipped tables whose source file it could not find, and
  could therefore report success for input it had never read. It now raises
  `SourceNotFound`.
- `extract_corpus` looked only for `*.xls` and so returned nothing at all,
  without complaint, for a directory of `.xlsx` files. Both suffixes are now
  accepted. This was the same fault already fixed in `verify`; a test written
  for coverage found the second instance of it.
- Section detection accepted only an ASCII period in a marker such as `1.本省人`.
  The compendium uses the full-width U+FF0E interchangeably, and the two are
  indistinguishable in print. 33 of the 353 tables tested in
  `docs/W06_layout.md` had their sections merged as a result: every figure
  correct, every attribution wrong. None of the affected tables is in the three
  chapters this package was written against, which is why it went unnoticed.
- The pattern for figures set inside a drawn brace matched only `└─N─┘`. The
  same brace is also drawn as `┌─N─┐`, `└──N──┘`, `└───────N───────┘` and with a
  single corner on one side, and those spellings were being discarded as
  unreadable. **102 figures in the published corpus are recovered by this fix.**
  No existing value changed. A braced missing marker, `└─.─┘`, is now read as
  missing rather than as unreadable, which keeps its row in the output.

### Changed
- `data/tidy.csv` grows from 36,570 to 36,672 rows, entirely from the brace fix
  above. The file in `data/` still holds the older extraction and is regenerated
  in W11.

### Added, continued
- `twstat sample` draws a blank coding sheet from a tidy CSV, stratified across
  sections, for the human check of `dim1` and `dim2` that the numeric
  verification cannot perform.
- `data/validation_sample.csv` — that sheet, 195 cells across all 65 sections,
  committed so a second coder can start without running anything.
- `docs/CODING_SHEET.md` — the instructions for that coder, self-contained.
- `docs/DESIGN.md`, `docs/EXAMPLE.md`, `docs/README.md`,
  `docs/W05_generalisation.md`, `docs/W06_layout.md`.
