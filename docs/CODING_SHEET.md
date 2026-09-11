# Instructions for a coder

`data/validation_sample.csv` is a blank coding sheet. This page is everything a
second coder needs; they do not have to read anything else in the repository.

## What this is for

Every number in `data/tidy.csv` has already been checked against the cell it came
from, mechanically and completely, so transcription is not in question. What is
in question is the labelling: whether `dim1` and `dim2` say what the printed
table says they say.

That cannot be checked mechanically. In these tables a label's characters are
distributed across the columns the label spans — 「大」 in one column and 「學」
three columns later, together meaning 大學 — so a program can assemble something
plausible and wrong, and no automated check will notice. It takes a person who
can read the printed layout.

One person doing it proves nothing, because they may simply repeat the
program's mistake. Two people doing it independently, and then measuring how
often they agree, is the point.

## What you will do

**Two to three hours.** 195 cells, three from each of the 65 sections, covering
all 48 tables and the years 1898 to 1944.

1. Get the source spreadsheets: `python scripts/download_raw.py`
2. Take a copy of `data/validation_sample.csv`. Name it after yourself.
3. For each row, open the file, go to the cell, and write down what the column
   means.
4. **Do not look at `data/tidy.csv`, and do not discuss rows with the other
   coder while coding.** If you have seen the pipeline's answer for a row, that
   row is spoiled and the exercise is worth less.

Each row gives you `table_id`, `section`, `year`, `src_row` and `src_col`. Row
and column numbers are 1-based, so `src_row 29, src_col 21` is row 29, column U.
The file for a `table_id` of `Mt468` is `raw/Edu_Mt468.xls`; the chapter prefix
is `Edu`, `Hygiene` or `Welfare`.

Fill in three columns:

| Column | What to write |
|---|---|
| `coded_dim1` | The outer heading the column falls under |
| `coded_dim2` | The inner heading, the one directly above the figures |
| `note` | Anything that made you hesitate. Optional, and useful |

## The rules, agreed before coding starts

These exist so that a disagreement between two coders means the layout is
genuinely ambiguous, rather than that the two of you were using different rules.

1. **Reassemble scattered characters according to the printed intent.** If 「大」
   sits above column 2 and 「學」 above column 4, and the two visibly form one
   heading spanning columns 2 to 4, that heading is 大學.
2. **When an outer heading is blank, carry the nearest non-blank heading to its
   left forward.** That is how the table is printed to be read.
3. **Some columns have no inner heading.** Leave `coded_dim2` blank. Blank is an
   answer; it is not the same as unclear.
4. **Write `UNCLEAR` when you cannot tell. Do not guess.** An honest `UNCLEAR` is
   information. A guess is noise that looks like agreement or disagreement at
   random.
5. **Copy the characters as printed.** Do not translate, do not modernise, do not
   normalise variant forms.
6. **Code the column, not the number.** 33 of the 195 cells are blank because the
   figure was not surveyed or was unknown. Those are coded like the rest — the
   heading is still printed above them. The value is shown only to help you
   confirm you are looking at the right cell.

## When both sheets are done

```python
import pandas as pd
from twstat.sampling import cohen_kappa

first = pd.read_csv("coding_alice.csv")
second = pd.read_csv("coding_bob.csv")

for column in ["coded_dim1", "coded_dim2"]:
    k = cohen_kappa(first[column].fillna(""), second[column].fillna(""))
    print(f"{column}: kappa = {k:.3f}")
```

Kappa is agreement corrected for the agreement two people would reach by chance.
1.0 is perfect; 0 is no better than chance; a negative value means the two coders
did worse than chance, which usually means one of them was applying a different
rule.

Then read the disagreements. They are the interesting part: each one is either a
rule that needed to be sharper or a place where the printed table really is
ambiguous, and both belong in the paper's limitations.

Last, compare the agreed coding against `data/tidy.csv`. That gives the rate at
which the pipeline's labels are right — which is the number this whole exercise
exists to produce, and which nobody can currently state.

## Reproducing the sheet

```bash
twstat sample data/tidy.csv data/validation_sample.csv
```

Seed 20260909, 195 rows, three per section. The same seed gives the same sheet.
Use `--size` and `--seed` for a different draw, and say which you used.

## Status

**Not yet done.** No second coder has been found. Until this exercise is carried
out, `dim1` and `dim2` in the published dataset have been read off the printed
layout by one person and checked by nobody, and the README, the codebook and
`DESIGN.md` all say so.
