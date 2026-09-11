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
services and poor relief — that is **39,150 rows, 30,640 values, 48 tables,
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
twstat notes raw data/notes.csv
twstat sample data/tidy.csv sheet.csv    # a blank coding sheet for a human checker
```

[`docs/EXAMPLE.md`](docs/EXAMPLE.md) walks through one table end to end — build
the sheet, write its specification, extract, verify, then break it and watch
verification pass on a result missing half its rows. No download needed.

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

Only `corpus1946` is about this particular compendium. How far the rest carries
over was tested rather than asserted, and the answer is mixed; see below.
[`docs/DESIGN.md`](docs/DESIGN.md) sets out the eleven decisions behind the
schema, the alternatives each was chosen over, and what each one costs.

**Column meanings are written by hand.** Automated header reconstruction was
attempted and abandoned, for reasons given below.

## What carries over to another source, and what does not

It is easy to claim that code written for one book is general. Everything below
was measured against material this package had never seen: two external corpora
published by Hitotsubashi University, and the 599 tables of the compendium's
other 21 chapters. `scripts/second_corpus.py` and `scripts/holdout.py` reproduce
every figure. The full accounts are in `docs/W05_generalisation.md` and
`docs/W06_layout.md`.

**The period taxonomy carries over.** The 年 / 年度 distinction — a calendar year
against a fiscal year running 1 April to 31 March — is not a quirk of this
compendium. Of 20,419 era expressions in the index to the Japanese Imperial
Statistical Yearbook, 1882–1940, the parser typed every one: 15,311 calendar
years and 5,108 fiscal years. Different government, different country, thirty
years earlier.

**The missing-value legend carries over within the compendium.** Across 473,293
cells of unseen chapters the proportions sit close to those in the chapters the
code was written against: 69.4% numbers against 74.3%, 24.0% missing against
18.4%.

**Resolving the Gregorian year does not carry over.** `eradate` reads the year
out of a parenthesised suffix, which 98.2% of this compendium's row labels carry
and the yearbook never prints. On the yearbook it resolved **0 years out of
33,116 labels**. It returns the period type and no year, which is the honest
answer, but anyone reusing this on a source dated by era alone will have to add
the arithmetic themselves. It is safe to do: the conversion agrees with the
printed year on all 59 labelled pairs in the yearbook and all 117 checkable
labels here. It is simply not needed for this corpus.

**Section handling is more specialised than it looks.** 11 of our 50 tables are
stacked, but only 20 of the other 599. Education, hygiene and welfare had their
categories reorganised repeatedly across fifty years, and the compilers cut such
tables into parts rather than merge them. The three chapters that motivated this
machinery are the three that need it most; on the rest of the book it does
nothing.

**One shape is out of scope entirely.** 152 of the 649 sections in the unseen
chapters — 23.4% — are cross-sectional snapshots with no dated rows at all, such
as a staffing table whose rows are job titles. The schema here begins with a
year, so these are refused rather than mangled. A quarter of the compendium
cannot be represented by this data model, and that is worth knowing before
planning to extend the dataset to the whole book.

## Six things that went wrong

These are in the repository because they are the argument for how the code is
now structured. Two were found by running the code on tables it had never seen,
and the last by a review of the code against the corpus, which is why both
exercises are worth the trouble. The full record, including the directions that
were investigated and dropped, is indexed in
[`docs/README.md`](docs/README.md).

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
verification could not catch it: every number was correct, and only its
attribution was wrong. The compilers had in fact documented the practice —
clause 7 of their notes says that categories which could not be merged were "cut
into several parts and listed separately" — which is a reminder that reading the
source's own front matter is not optional.

**The verifier had two faults of its own.** It compared source cells with a bare
`float()` rather than the parsing rules the extraction used, and so reported the
`└─N─┘` typesetting artifacts as data errors. It also skipped tables whose source
file it could not find, meaning it could return "no mismatches" for input it had
never read. Both are fixed; the second now raises rather than passing quietly.

**A full stop defeated section detection.** Stacked tables are marked `1.本省人`.
The detector required an ASCII period; the compilers also used the full-width
U+FF0E, `１．官等`, and in print the two are the same character. 117 markers in
102 of the 599 unseen tables went unread, and in 6 of those files that merged
two sections into one — the same failure as above, again invisible to any check
on values. None of the 102 is in the chapters used here, which is exactly why it
survived.

**The brace pattern matched one spelling out of several.** A figure spanning
several printed columns is set inside a drawn brace which the digitisation kept
in the cell. The pattern matched `└─42─┘` but not `┌─1─┐`, `└──126──┘` or
`└───────76───────┘`, and those figures were discarded as unreadable. Unlike the
one above, this was not confined to the unseen chapters: **98 figures in the
published corpus were being thrown away**, and `data/tidy.csv` gains 102 rows.
No value was wrong, so verification passed; the values simply were not there.

**Three health tables published the wrong disease names.** They run five or six
bands of column headings down one sheet, each re-using the same columns for
different diseases, and nothing marks the boundaries. The pipeline applied the
first band's headings to the whole section. **2,976 rows — 8.1% of the dataset —
named a disease belonging to a different disease**, and a count of pulmonary
tuberculosis was published as paratyphoid. Verification reported no mismatches
throughout, correctly: every number was read from the right cell. Only the label
was wrong, and a check on values cannot see a label. This is the same lesson as
the stacked sections above, learned a second time in a form the first fix did
not cover. [`docs/W13_header_bands.md`](docs/W13_header_bands.md) is the full
account.

## What is not verified

The numeric layer is checked completely. **The semantic layer is not.** Which
dimension a column belongs to was read off the printed layout by one person, and
no second reader has confirmed it. Until that is done, treat `dim1` and `dim2` as
proposed rather than established.

The work is set up and waiting for someone to do it.
[`data/validation_sample.csv`](data/validation_sample.csv) is the blank coding
sheet — 234 cells, three from each of the 78 sections, all 48 tables — and
[`docs/CODING_SHEET.md`](docs/CODING_SHEET.md) is everything a second coder needs
in one page: the rules agreed in advance, how to fill it in, and how to compute
Cohen's kappa afterwards. Two to three hours.

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
