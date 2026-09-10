# Remaining work

Status: [ ] open · [x] done · [!] dropped, with a reason

## Tooling
- [x] W01 Add ruff for linting and formatting; fix what it reports
- [x] W02 Add mypy; annotate until it passes on `src/`
- [x] W03 Raise coverage where it is thin: notes 38%, cli 0%, verify 85%
- [x] W04 Extend CI with lint and type-check jobs

## Generalisation
- [ ] W05 Find a second corpus and test `eradate` against it
- [ ] W06 Test `sections` and `values` against that corpus; record what breaks
- [ ] W07 State plainly in the docs which parts are corpus-agnostic

## Documentation
- [ ] W08 Add an index to `docs/` so the investigation record is navigable
- [ ] W09 Write `docs/DESIGN.md` on the decisions and their trade-offs
- [ ] W10 Add a short worked example a newcomer can follow

## Data
- [ ] W11 Regenerate `data/tidy.csv` and `data/notes.csv` from the package
- [ ] W12 Produce the validation coding sheet as a committed artefact
