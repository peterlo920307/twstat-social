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
- `data/validation_sample.csv` — that sheet, 234 cells across all 78 sections,
  committed so a second coder can start without running anything.
- `docs/CODING_SHEET.md` — the instructions for that coder, self-contained.
- `docs/DESIGN.md`, `docs/EXAMPLE.md`, `docs/README.md`,
  `docs/W05_generalisation.md`, `docs/W06_layout.md`.

### Fixed, data correctness
- **Three health tables were publishing the wrong disease names.** Mt487-2,
  Mt488 section 2 and Mt489 section 2 each run five or six bands of column
  headings down one sheet, each band re-using the same columns for a different
  set of diseases, with nothing marking the boundaries. The pipeline applied the
  first band's headings to the whole section, so **2,976 rows — 8.1% of the
  dataset — named a disease belonging to a different disease**: a count of
  pulmonary tuberculosis was published as paratyphoid. `verify` reported no
  mismatches throughout, correctly, because every number was read from the right
  cell. `sections.find` now splits on a fresh header band as well as on a
  numbered marker, and those three files gain 13 sections between them.
  `docs/W13_header_bands.md` is the account.
- A figure printed with the compilers' own footnote marker in front of it,
  `(1)    10`, was rejected as unreadable and its row dropped. 23 figures across
  seven tables are recovered.
- `Edu_Mt480` gives 共計, 中日文 and 外國文 on the upper header row rather than
  the innermost one, so all three columns published with no second dimension and
  117 rows became indistinguishable triplets. The specification states them now.
- `tests/test_corpus.py` asserts that no `(table_id, section, year, dim1, dim2)`
  key carries two different values, and that no source cell is used twice. The
  first would have failed on 726 keys before these fixes. The project had a
  complete check of values and no check of whether two rows claimed to describe
  the same thing.

### Changed, data
- `data/tidy.csv`: 36,672 to 36,735 rows, 28,667 to 28,745 values, 65 to 78
  specified sections. Verification still reports no mismatches.
- `data/validation_sample.csv` redrawn against the corrected data: 234 cells,
  three from each of the 78 sections.

### Known, not fixed
- Mt487-2 and Mt489 pair each year across two rows, `┌患者` and `└死亡`, and only
  the first carries a year. The second is skipped and **about 1,900 figures are
  discarded**. The surviving rows are case counts and the schema does not say so.
  Recorded in `docs/bias_statement.md` B7.

### Fixed, source corrections
- `Welfare_Mt504` printed 民國前九年 as `(1093)`. The row gave no year and was
  skipped in silence, which is the whole of what `bias_statement.md` used to
  describe as the dataset's one internal coverage gap. `SpecBook.correct_year`
  records it as 1903, with the evidence, and the extractor now refuses any row
  label that looks dated but yields no year rather than skipping it. There are
  no internal year gaps left.
- Table 491 is a death rate, and its own footnote says a printed 0 means cases
  and no deaths. Its 46 zeros were flagged `less_than_one_unit` under the
  compilers' general legend; they are exact zeros, and
  `SpecBook.zero_is_exact` records that the footnote overrides the legend.
  `less_than_one_unit` now marks one cell, in Mt502.
- Section labels had a private-use character left by the 2006 digitisation,
  and a full-width marker stop was not stripped from them.

### Fixed, recovered figures
- Mt487-2 and Mt489 split each year across two rows, `┌患者` and `└死亡`, with
  the year printed only on the first. The second row was skipped, **1,895
  figures were discarded**, and the surviving rows were case counts with nothing
  in the schema to say so. The year is now carried to the row a brace joins, and
  患者 or 死亡 goes into `dim2`, which these tables had left empty. An orphan
  `└` row is not given a year. This closes the "Known, not fixed" entry above.
- `data/tidy.csv`: 36,752 to 39,150 rows, 28,745 to 30,640 values. The shares of
  period types move with it: 41% calendar year, 37% fiscal, 22% year end.
