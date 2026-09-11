# A worked example

Fifteen minutes, no corpus download, no Chinese needed. You build one small
spreadsheet that has every awkward feature the real ones have, turn it into tidy
data, and then watch verification pass on a result that is missing half its rows.

Everything here is run as a test in `tests/test_example.py`, so if the code
changes and this page stops being true, the suite fails.

## 1. Build the sheet

```python
import pandas as pd

rows = [
    ["表900  歷  年  某  校  概  況", None, None, None],
    [None, None, None, None],
    ["1.本省人", None, None, None],
    [None, "公", None, "立"],
    [None, "校數", "教員數", "學生數"],
    ["民國前 十 三 年度底(1899)", 1, 10, "└─69─┘"],
    ["十 二 年度底(1900)", 1, ".", 89],
    ["十 一 年度底(1901)", 0, 15, 107],
    [None, None, None, None],
    ["2.日本人", None, None, None],
    [None, "公", None, "立"],
    [None, "校數", "教員數", "學生數"],
    ["民國前 十 三 年度底(1899)", 2, 20, 300],
    ["十 二 年度底(1900)", 2, 22, 340],
    ["附註:(1)本表為示範用途而編造,非原書資料.", None, None, None],
]
pd.DataFrame(rows).to_excel("Demo_Mt900.xlsx", header=False, index=False)
```

## 2. Read what is wrong with it

Nine things, and every one of them occurs in the real corpus.

| Where | What |
|---|---|
| Row 1 | The title has spaces inside the words, for justification |
| Rows 3, 10 | **Two tables stacked in one sheet**, each with its own header |
| Row 4 | 公 sits in column 2 and 立 in column 4. Together they read 公立 — the label's characters are spread across the columns it spans |
| Row 6 | The year is `民國前 十 三 年度底(1899)`: era reckoning, spaces inside the numeral, the reporting convention in words, the Gregorian year in brackets |
| Row 6 | 年度底 is a **fiscal year end**, 31 March 1900, not 31 December 1899 |
| Row 6 col 4 | `└─69─┘` is 69 inside a brace the printer drew across merged columns |
| Row 7 col 3 | `.` is not zero. It was either not surveyed or unknown, and the digitisation lost which |
| Row 8 col 2 | `0` is not zero either. The compilers' legend says it means **less than one unit** |
| Row 15 | A footnote, which belongs to the second table and not the first |

There are no column names anywhere. A person reading the printed page has no
trouble; a program has nothing to go on.

## 3. Say what the columns mean

This is the part that is not automated, and section 4 of
[`DESIGN.md`](DESIGN.md) explains why an attempt to automate it produced
confident wrong answers.

```python
from twstat.spec import SpecBook

book = SpecBook()
for number, group in [(1, "本省人"), (2, "日本人")]:
    book.section("Demo_Mt900", number).add_range(2, 4, group)
```

Two statements, and that is the whole specification. `add_range(2, 4, group)`
says columns 2 to 4 all belong to this group. Nothing says what `校數`, `教員數`
and `學生數` are, because those are printed in the sheet and will be read from
it — that is what `dim2=None` means, and it is the default.

## 4. Extract

```python
from twstat import extract_corpus

tidy = extract_corpus(".", book)
```

Fifteen rows, the first ten shown:

```
table_id  section section_label  year     period_type dim1 dim2  value               flag  src_row  src_col
   Mt900        1           本省人  1899 fiscal_year_end  本省人   校數    1.0                NaN        6        2
   Mt900        1           本省人  1899 fiscal_year_end  本省人  教員數   10.0                NaN        6        3
   Mt900        1           本省人  1899 fiscal_year_end  本省人  學生數   69.0   bracket_artifact        6        4
   Mt900        1           本省人  1900 fiscal_year_end  本省人   校數    1.0                NaN        7        2
   Mt900        1           本省人  1900 fiscal_year_end  本省人  教員數    NaN            missing        7        3
   Mt900        1           本省人  1900 fiscal_year_end  本省人  學生數   89.0                NaN        7        4
   Mt900        1           本省人  1901 fiscal_year_end  本省人   校數    0.0 less_than_one_unit        8        2
   Mt900        1           本省人  1901 fiscal_year_end  本省人  教員數   15.0                NaN        8        3
   Mt900        1           本省人  1901 fiscal_year_end  本省人  學生數  107.0                NaN        8        4
   Mt900        2           日本人  1899 fiscal_year_end  日本人   校數    2.0                NaN       13        2
   ...
```

Read across one row and you can check the whole chain yourself. The third row
says: the figure 69 is a count of students in the Taiwanese section, for the
fiscal year ending 31 March 1900, and it came from row 6 column 4 of the sheet,
where it was printed inside a brace. Open the file at that cell and there it is.

The three awkward cells came out as they should:

- `└─69─┘` → `69.0`, flagged `bracket_artifact` so you know the brace was there
- `.` → no value, flagged `missing`
- `0` → `0.0`, flagged `less_than_one_unit`, **not** treated as a plain zero

## 5. Verify

```python
from twstat import verify

assert verify(tidy, ".") == []
```

This is not a sample. It reopens the spreadsheet, goes to the cell named by
`src_row` and `src_col`, applies the same reading rules, and compares. Fourteen
of the fifteen rows carry a number; the fifteenth is the missing marker at row 7,
which has nothing to compare against. Fourteen out of fourteen.

## 6. Now break it, and watch verification pass anyway

Specify one section where the sheet has two:

```python
half = SpecBook()
half.section("Demo_Mt900", 1).add_range(2, 4, "學校")

tidy = extract_corpus(".", half)
len(tidy)             # 9, not 15
verify(tidy, ".")     # []
```

Six observations are gone and the verifier is perfectly happy, because every
value it can see is correct. **It checks that what is there is right. It cannot
check that what should be there is there.**

That is not a hypothetical. Before section handling existed, this pipeline
merged Taiwanese and Japanese populations into single series in two real
education tables, and passed every check it had. Seven tables already reported
finished had to be redone. [`D15_section_bug.md`](D15_section_bug.md) is the
record.

You have just watched it happen on nine rows. It happened on two real education
tables for as long as it took someone to notice.

## 7. The footnotes

```python
from twstat.notes import extract_notes

notes = extract_notes("Demo_Mt900.xlsx")
```

One note, and it is attached to section 2 — the table it sits under — rather than
to the file as a whole. In the real corpus this matters: a footnote to one
education table records that indigenous children were not counted in the
school-age population before 1921, which is a break in the series that nothing in
the numbers reveals.

## Where to go next

- [`CODEBOOK.md`](CODEBOOK.md) — every column and every allowed value
- [`DESIGN.md`](DESIGN.md) — why the schema is shaped this way, and what it costs
- [`../README.md`](../README.md) — what carries over to a different source
- `twstat.corpus1946` — the same exercise done 65 times, by hand
