## What this changes

<!-- One or two sentences. If it changes what data/ contains, say how many rows or
values move and why. -->

## Checks

- [ ] `python -m ruff check src tests scripts` and `python -m ruff format --check src tests scripts`
- [ ] `python -m mypy`
- [ ] `python -m pytest -q` with `raw/` present, not only the CI subset
- [ ] If a reading rule changed: regenerated the data and verified it
      ```bash
      twstat extract raw data/tidy.csv && twstat verify data/tidy.csv raw
      twstat notes raw data/notes.csv --items data/note_items.csv
      twstat sample data/tidy.csv data/validation_sample.csv --size 240
      ```
- [ ] If figures in the documentation moved: updated them (the tests in
      `tests/test_published_data.py` catch the headline ones, not all of them)
- [ ] `CHANGELOG.md` says what a user of the data needs to know
