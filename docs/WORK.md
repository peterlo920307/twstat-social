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
- [ ] W12 Produce the validation coding sheet as a committed artefact
