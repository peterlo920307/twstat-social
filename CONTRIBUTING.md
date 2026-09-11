# Contributing

Issues and pull requests are welcome at
<https://github.com/peterlo920307/twstat-social>.

## Getting set up

```bash
git clone https://github.com/peterlo920307/twstat-social
cd twstat-social
pip install -e ".[dev]"
pytest
```

The tests marked `corpus` need the source spreadsheets, which are not kept in
version control. Fetch them with `python scripts/download_raw.py`, or run
`pytest -m "not corpus"` to skip them, which is what CI does.

## What is most useful

**Column specifications.** `src/twstat/corpus1946.py` says which spreadsheet
columns carry which dimensions. Every entry was read off the printed layout by
one person and none has been independently checked. If you read Chinese and
find an entry that misreads a table, an issue naming the file, section and
column is worth more than any amount of new code. See `docs/validation_plan.md`
for how the checking is meant to work.

**Other corpora.** The code was written for one 1946 compendium. How far it
carries has been measured rather than assumed: the reporting-period taxonomy
holds on an independent Japanese source, resolving the Gregorian year does not,
and section handling is mostly needed in the three chapters it was written for.
`docs/W05_generalisation.md` and `docs/W06_layout.md` give the numbers. Reports
of where it breaks on other sources are welcome, with a sample.

## Conventions

- Code is formatted at 100 columns and type-annotated.
- New behaviour needs a test. Tests use examples drawn from the corpus rather
  than invented input, so that a regression shows up against something real.
- Anything that changes extracted values must keep `twstat verify` clean.

## Reporting problems

Use the issue forms: one for a figure or label that disagrees with the source,
which asks for the `table_id`, `src_row` and `src_col` that let it be checked, one
for code that does not work, and one for questions about the source. For
questions about the data rather than the code, the codebook (`docs/CODEBOOK.md`)
and the statement of what the data cannot support (`docs/bias_statement.md`) may
already answer them.

A pull request fills in a short checklist; the one item people forget is
regenerating `data/` when a change moves what is extracted.

Conduct is covered by `CODE_OF_CONDUCT.md`, and anything that looks like a
security problem by `SECURITY.md` rather than a public issue.
