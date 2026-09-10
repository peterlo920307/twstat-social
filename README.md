# twstat

Recovering usable data from legacy East Asian statistical tables.

[![tests](https://github.com/peterlo920307/twstat-social/actions/workflows/tests.yml/badge.svg)](https://github.com/peterlo920307/twstat-social/actions/workflows/tests.yml)

The corpus this was built for is the *Taiwan Province Statistical Abstract for
the Past Fifty-One Years*, compiled in 1946 from 1,207 Japanese colonial
publications and digitised by Academia Sinica in 2006 as several hundred Excel
files. The files preserve the printed layout faithfully, which is precisely the
problem: they are legible to a reader and close to meaningless to a program.

```
raw/Edu_Mt468.xls, rows 5-8
             0   1    2    3     4    5    6     7
4          NaN   大  NaN    學   專…  NaN  NaN   師…    label characters spread
5          NaN  校數  教員數  學生數    校數  教員數  學生數   校數      across the columns they span
6  民國前 十 三…   .    .    .     1   10   69     1    "." is absent, not zero
7        十 …    .    .    .     1   11   89     1    the year sits inside prose
```

There are no column names. The year is written `民國前 十 三 年度底(1899)`, with
spaces inside the numeral and the reporting convention appended in words. A
printed `0` does not mean zero. Several unrelated tables may be stacked in one
sheet, each with its own header and sometimes a shifted column layout.

## What it produces

```
table_id  section  year  period_type      dim1   dim2  value  flag     src_row  src_col
Mt468     1        1899  fiscal_year_end  大學    校數    NaN   missing  7        2
Mt468     1        1899  fiscal_year_end  專門學校  校數    1.0   NaN      7        5
Mt468     1        1899  fiscal_year_end  專門學校  教員數   10.0  NaN      7        6
```

One row per observation, carrying the cell it was read from. That last part is
what makes the result checkable: every number can be read back from the source
and compared, so the claim is a complete check rather than an accuracy estimate.

For the three sections of the compendium processed here — education, health
services and poor relief — that is **36,570 rows, 28,569 values, 48 tables,
1897–1945, and no mismatches**.

## Install

```bash
pip install -e ".[dev]"
```

## Use

```bash
python scripts/download_raw.py           # fetch the sources from Academia Sinica
twstat extract raw data/tidy.csv
twstat verify data/tidy.csv raw
```

Or as a library, against any similar corpus:

```python
from twstat import extract_corpus, verify
from twstat.spec import SpecBook

book = SpecBook()
book.define("Edu_Mt468", 1, [(2, 4, "大學"), (5, 7, "專門學校")])

tidy = extract_corpus("raw", book)
assert verify(tidy, "raw") == []
```

## Design

The package separates the parts that generalise from the part that does not.

| Module | Concern |
|---|---|
| `eradate` | Era years and the four reporting conventions |
| `values` | Cell semantics, including the source's missing-value legend |
| `sections` | Several tables stacked in one sheet |
| `spec` | Which columns mean what |
| `extract` | Assembling tidy rows |
| `verify` | Reading every value back from its source cell |
| `notes` | The compilers' own footnotes |
| `sampling` | Coding sheets and inter-coder agreement |
| `corpus1946` | The specifications for this particular compendium |

Everything except `corpus1946` describes conventions of Japanese and
Republican-era statistical publishing rather than one book.

**Column meanings are written by hand.** Automated header reconstruction was
attempted and abandoned, for reasons given below.

## Three things that went wrong

These are in the repository because they are the argument for how the code is
now structured.

**Automated header reconstruction produced plausible wrong answers.** Because a
label's characters are distributed across the columns it spans, they can be
reassembled by following the innermost header's repeat period. A quick check —
"are there any single-character labels left?" — reported 12 of 16 tables clean.
Inspection showed most were wrong: `學生` and `年度中學生異動` had been fused into
one label, and in one table the title had been absorbed into a column name. The
check was a bad proxy, and the failures were invisible to it. Column meanings
have been written by hand since.

**Stacked sections went undetected.** Eleven of the fifty files contain several
tables one below another. Before this was noticed, two education tables had
their Taiwanese and Japanese populations merged into single series. Value-level
verification could not catch it: every number was correct, and only their
attribution was wrong. The compilers had in fact documented the practice —
clause 7 of their notes says that categories which could not be merged were "cut
into several parts and listed separately" — which is a reminder that reading the
source's own front matter is not optional.

**The verifier had two faults of its own.** It compared source cells with a bare
`float()` rather than the parsing rules the extraction used, and so reported the
`└─N─┘` typesetting artifacts as data errors. It also skipped tables whose source
file it could not find, meaning it could return "no mismatches" for input it had
never read. Both are fixed; the second now raises rather than passing quietly.

## What is not verified

The numeric layer is checked completely. **The semantic layer is not.** Which
dimension a column belongs to was read off the printed layout by one person, and
no second reader has confirmed it. `twstat.sampling` produces the coding sheets
for doing that properly; `docs/validation_plan.md` describes the procedure.
Until it is done, treat `dim1` and `dim2` as proposed rather than established.

## Source and licensing

*Taiwan Province Statistical Abstract for the Past Fifty-One Years* (1894–1945),
compiled 1946 by the Statistical Office of the Taiwan Provincial Administrative
Executive Office. Digitised by the Institute of Information Science, Academia
Sinica: <http://twstudy.iis.sinica.edu.tw/twstatistic50/>.

The compendium is a government document and under Article 9 of the Copyright Act
of the Republic of China is not subject to copyright; the figures are facts. The
source spreadsheets are not redistributed here — `scripts/download_raw.py`
fetches them.

Code: MIT (`LICENSE`). Data and documentation: CC BY 4.0 (`LICENSE-DATA`).
