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
