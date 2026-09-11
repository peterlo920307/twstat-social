# Remaining work

Status: [ ] open · [x] done · [!] dropped, with a reason

## Tooling
- [x] W01 Add ruff for linting and formatting; fix what it reports
- [x] W02 Add mypy; annotate until it passes on `src/`
- [x] W03 Raise coverage where it is thin: notes 38%, cli 0%, verify 85%
- [x] W04 Extend CI with lint and type-check jobs

## Generalisation
- [x] W05 Find a second corpus and test `eradate` against it — docs/W05_generalisation.md
- [x] W06 Test `sections` and `values` against that corpus; record what breaks — docs/W06_layout.md
- [x] W07 State plainly in the docs which parts are corpus-agnostic — README "What carries over"

## Documentation
- [x] W08 Add an index to `docs/` so the investigation record is navigable
- [x] W09 Write `docs/DESIGN.md` on the decisions and their trade-offs
- [x] W10 Add a short worked example a newcomer can follow — docs/EXAMPLE.md

## Data
- [x] W11 Regenerate `data/tidy.csv` and `data/notes.csv` from the package
- [x] W12 Produce the validation coding sheet as a committed artefact — data/validation_sample.csv

---

All twelve are done. What remains is not engineering.

## Blocked on a person

- **A second coder.** `data/validation_sample.csv` is drawn and
  [`CODING_SHEET.md`](CODING_SHEET.md) tells them everything they need. Two to
  three hours. Until this happens `dim1` and `dim2` are machine-proposed, which
  is the largest single caveat on the dataset and is stated in the README, the
  codebook and `DESIGN.md`.

## Blocked on a decision that is not mine

- **Whether the repository goes public.** Nothing here needs to stay private,
  but that is the owner's call.
- **Whether to deposit.** [`zenodo_workflow.md`](zenodo_workflow.md) has the
  order of operations. A DOI has to exist before submission, not after.

## Waiting on the above

- `.zenodo.json` has 7 placeholders: author, ORCID, date, description, method.
- [`JOHD_draft.md`](JOHD_draft.md) has 19. Most need the kappa figure, the DOI,
  or an author decision rather than more work on the data.

## Worth doing, nobody is asking for it

- Extend beyond the three chapters. 599 tables are downloadable and the code now
  reads them; what is missing is 500-odd hand-written column specifications.
  [`W06_layout.md`](W06_layout.md) says what to expect, including that a quarter
  of them are cross-sectional and outside this schema entirely.
- Recover the distinction between 「－」 and 「…」, which the 2006 digitisation
  collapsed. Only the printed book can settle it.
