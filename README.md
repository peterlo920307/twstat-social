# twstat-social

**Colonial Taiwan social-administration statistics, 1895–1945** — education,
health services and poor relief, recovered from legacy spreadsheets into a tidy,
verifiable dataset.

**36,570 rows · 28,569 values · 48 tables · 65 sections · 1897–1945 · 0 verification failures**

---

## The problem

In 1946 the incoming Taiwanese Provincial Administrative Executive Office compiled
*Taiwan Province Statistical Abstract for the Past Fifty-One Years*, condensing 1,207
Japanese colonial statistical publications into 540 tables. Academia Sinica digitised
it in 2006 as ~650 Excel files and put them online.

The files are readable by humans and useless to machines:

```
raw/Edu_Mt468.xls, rows 5–8
             0   1    2    3     4    5    6     7
4          NaN   大  NaN    學   專…  NaN  NaN   師…      ← label characters
5          NaN  校數  教員數  學生數    校數  教員數  學生數   校數        scattered across cells
6  民國前 十 三…   .    .    .     1   10   69     1      ← "." is not zero
7        十 …    .    .    .     1   11   89     1      ← year buried in prose
```

There are no column names, the year is written as `民國前 十 三 年度底(1899)` with
spaces inside the numeral, `.` means missing, and several unrelated tables are stacked
inside one file.

## What this produces

```
table_id  year  period_type      dim1   dim2  value  flag         src_row  src_col
Mt468     1899  fiscal_year_end  大學    校數    NaN   missing_dot  7        2
Mt468     1899  fiscal_year_end  專門學校  校數    1.0   NaN          7        5
Mt468     1899  fiscal_year_end  專門學校  教員數   10.0  NaN          7        6
```

One row per observation, with the originating cell recorded so every value can be
traced back and re-checked.

## What it took

| Problem | Handling |
|---|---|
| Label characters scattered across cells | Per-table specifications, reviewed by hand |
| Multiple tables stacked in one file | `sections.py` — 11 of 50 files affected |
| `民國前十五年(1897)`, spaces inside numerals | `normalize.py` — 91% resolved automatically |
| Four different period bases | `period_type`: calendar / year-end / fiscal / fiscal-year-end |
| `.` = missing, `0` = *less than one unit* | Distinct flags; `0` is **not** zero |
| `└─42─┘` merged-cell artifacts | Value extracted, flagged |

Every numeric value is checked back against its source cell:
**0 mismatches out of 28,569.**

## Quick start

```bash
pip install pandas openpyxl xlrd
python scripts/download_raw.py        # fetch the 50 source files from Academia Sinica
python scripts/apply_spec.py          # write column specifications into the worksheet
python scripts/apply_v2.py docs/header_worksheet_v2.csv raw data/tidy.csv
```

Verify:

```python
from make_validation_sample import auto_verify
auto_verify("data/tidy.csv", "raw")   # -> []
```

## Layout

```
scripts/     normalize.py  sections.py  build_worksheet.py
             spec_v2.py  apply_spec.py  apply_v2.py
             extract_notes.py  make_validation_sample.py  download_raw.py
data/        tidy.csv (36,570 rows)   notes.csv (102 footnotes)
docs/        CODEBOOK.md  bias_statement.md  validation_plan.md
             header_worksheet_v2.csv  + investigation log
raw/         not in version control — see scripts/download_raw.py
```

## Three things that went wrong

Documented in full under `docs/`, because they are the reason the column
specifications are written by hand rather than inferred.

1. **Automated header reconstruction produced plausible but wrong labels.** A naive
   check ("no single-character labels") passed 12 of 16 tables; inspection showed most
   were wrong — `學生` and `年度中學生異動` had been fused into one label, and a table
   title had been absorbed into a column name. Bad proxy metric, silent failure.
2. **Stacked sections went undetected.** Eleven files contain several tables one below
   another. Before this was noticed, Taiwanese and Japanese populations in two education
   tables had been merged into a single series. Value-level verification could not catch
   it — the numbers were all correct; only their meaning was wrong.
3. **The verifier had a bug.** `auto_verify` compared raw cells with `float()` without
   applying the pipeline's own parsing rules, so `└─42─┘` was reported as a data error.
   Verification code needs verifying too.

## Status

The numeric layer is fully verified. The **semantic layer — what each column means —
is machine-proposed and not yet independently checked by a second person.** See
`docs/validation_plan.md`.

## Source and licensing

*Taiwan Province Statistical Abstract for the Past Fifty-One Years* (1894–1945),
compiled 1946 by the Statistical Office of the Taiwan Provincial Administrative
Executive Office; digitised by the Institute of Information Science, Academia Sinica
(http://twstudy.iis.sinica.edu.tw/twstatistic50/).

The source is a government document and, under Article 9 of the Copyright Act of the
Republic of China, not subject to copyright; the values are facts. The source `.xls`
files are not redistributed here — `scripts/download_raw.py` fetches them.

Code: MIT (`LICENSE`) · Data and documentation: CC BY 4.0 (`LICENSE-DATA`)
