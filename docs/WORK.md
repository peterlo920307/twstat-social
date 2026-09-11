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

## Found by the reviews of 11 September, not yet done

Eight parallel reviews of the code, data, tests, packaging, scripts and prose.
What they found that is fixed is in the changelog; this is what is not.

- [ ] R01 **Mt487-2 and Mt489 discard about 1,900 figures.** Each year is paired
      across two rows, `┌患者` and `└死亡`, and only the first carries a year, so
      the death row is skipped. Needs the year carried across a continuation row
      and a row-level dimension in the schema. `bias_statement.md` B7.
- [x] R02 **`verify` never reads back the 8,005 rows with no value.** Their
      provenance is never dereferenced, so a wrong coordinate on a missing row is
      undetectable — setting every one to row 9999 still reports zero mismatches.
      It should check that the cell really is unreadable.
- [ ] R03 **The test suite kills no mutants.** Thirty deliberate defects were
      introduced one at a time; the CI suite caught none of them and the full
      suite caught twelve. 99% line coverage, and `verify`'s 1e-9 tolerance,
      `header_rows`' title filter and every heuristic in `extract_notes` are
      unasserted. Coverage was measuring the wrong thing.
- [ ] R04 **`Welfare_Mt504` loses a whole year to a source typo.** The compendium
      prints 民國前九年's Gregorian gloss as `(1093)` for 1903. The year fails to
      parse and the row is skipped in silence — the one internal coverage hole in
      the corpus. Needs an errata entry and a refusal to skip a stub that looks
      dated.
- [ ] R05 **`less_than_one_unit` is probably wrong for 46 of its 47 cells.**
      Clause 11 says a printed `0` means below one unit, but Mt491's own footnote
      says its `0` means "there were patients but no deaths" — an exact zero. The
      flag needs to be settable per table.
- [ ] R06 **The download scripts accept an error page as data.** The Sinica host
      is behind a WAF that returns HTTP 200 with an HTML page; every script
      writes it to `raw/` and reports success. Needs a magic-byte and length
      check, atomic writes via a `.part` file, and a checksum manifest.
- [ ] R07 `verify` is 5× slower than it needs to be and the suite 2.3×, both from
      `iterrows` and `.iat` boxing a pandas object per cell. Measured, with
      byte-identical output. Worth doing, not urgent.
- [ ] R08 Prose and consistency: the long tail from the copy-editing review that
      the factual corrections did not already cover.

---

The original twelve are done. What remains beyond the list above is not
engineering.

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
