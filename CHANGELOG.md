# Changelog

## 0.1.0 — unreleased

First packaged version. The extraction previously lived in a set of loose
scripts; it is now a library with a command line entry point, a complete check
of every value against its source cell, and structural checks the scripts never
had. Several defects in the scripts' output were found and fixed on the way,
three of them serious enough that anyone holding an earlier draft of the data
should replace it; they are listed under Fixed.

### Added
- `twstat.eradate` — era-year and reporting-period parsing.
- `twstat.values` — cell semantics, including the compilers' own legend, in
  which a printed `0` means a quantity below one unit.
- `twstat.sections` — detection of several tables in one sheet, whether marked
  by a numbered heading or only by a fresh band of column headings.
- `twstat.spec` — column specifications, with an explicit distinction between
  "take the innermost header" and "this column has no second dimension", and
  two kinds of source correction: `correct_year` for a misprinted Gregorian
  year, and `zero_is_exact` for a table whose own footnote overrides the legend.
- `twstat.extract`, `twstat.verify` — extraction, and a check that re-reads
  every row from the cell it came from, including rows with no value.
- `twstat.notes` — the compilers' footnotes and source attributions, and
  `note_items`, which splits notes into numbered items so a label's `(1)` can be
  joined to its footnote.
- `twstat.sampling` — stratified coding sheets and Cohen's kappa.
- `twstat` command: `extract`, `verify`, `notes` (with `--items`), `sample`.
- Data: `tidy.csv`, `notes.csv`, `note_items.csv`, and `validation_sample.csv`,
  a blank coding sheet of 234 cells across all 78 sections.
- Documentation: `DESIGN.md`, `EXAMPLE.md`, `CODING_SHEET.md`, an index to the
  investigation record, and the two generalisation studies.
- Reproduction: download scripts that check what they fetch against a checksum
  manifest and refuse an error page, and two scripts that re-run the
  generalisation studies.

### Fixed — in the data
- **Three health tables published the wrong disease names.** Mt487-2, Mt488 and
  Mt489 run five or six bands of column headings down one sheet with nothing
  marking the boundaries, and the first band's names were applied to the whole
  section: 2,976 rows named a disease belonging to another, and a count of
  pulmonary tuberculosis was published as paratyphoid. `docs/W13_header_bands.md`.
- **1,895 death counts were missing.** Mt487-2 and Mt489 split each year into a
  cases row and a deaths row, and only the first carries the year, so the second
  was skipped and what remained was cases alone.
- **A braced figure was credited to one column when it spans several.** The
  spanned cells were flagged missing, so table 507's 646 temples, halls and
  神明會 for 臺北州 in 1909 read as 646 temples. They are now `covered`.
- 98 figures set inside a drawn brace in a spelling other than `└─N─┘`, and 23
  printed with a footnote marker in front, were discarded as unreadable.
- Mt480's three volume columns shared one key and became indistinguishable.
- Mt504's misprinted `(1093)` made its 1903 row vanish, and this was reported as
  the dataset's one internal year gap. It is corrected to 1903, with the
  evidence recorded, and there are no internal gaps.
- Table 491's zeros are exact, by its own footnote, not below one unit.
- `missing` now means the compilers' dot only; an empty cell is `blank`.

### Fixed — in the code
- Section markers written with the full-width stop `．` were not recognised: 117
  markers across 102 of 599 unseen tables, merging two sections in six files.
- Every place that listed spreadsheet files matched `*.xls` only, or matched
  case-sensitively, and returned nothing without complaint for other names.
  Found four times; the last instance had changed a published figure.
- `verify` compared cells with a bare `float()`, skipped tables whose source it
  could not find, skipped every row with no value, and accepted coordinates of
  zero, which pandas reads as the last row of the sheet.
- A footnote could run on into the heading of the next section.
- A row label that looks dated but gives no year now raises instead of being
  skipped.

### Changed
- Against the scripts it replaces: 36,570 rows to 39,150, 28,569 values to
  30,640, 65 specified sections to 78. `verify` reports no mismatches, no key
  carries two values, no source cell is used twice, and every footnote
  reference in a label resolves.

### Known
- The column labels have been read off the printed layout by one person and
  checked by nobody. `docs/CODING_SHEET.md` sets out the check.
- The limits of the source are in `docs/bias_statement.md`: the 1943 collapse,
  who was not counted, the re-dating into Republican reckoning, the 21 ratio
  columns computed during digitisation, and the rest.
