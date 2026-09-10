# Design decisions and what they cost

Each decision below is stated with the alternative it was chosen over, what it
costs, and what would change it. Several were made twice, because the first
version was wrong; those are marked.

## 1. Every row carries the cell it came from

`src_row` and `src_col` name the spreadsheet cell each value was read from. The
alternative is a tidy table with no provenance, which is what most published
historical datasets are.

The cost is real: the two columns are about a fifth of the file, and 36,672 rows
of ten columns is 2.9 MB where the values alone would be a fraction of that.

They buy the only claim in this project that is worth anything. `twstat verify`
re-reads every value from its source cell and compares. Not a sample, not an
estimate — all 28,667 of them, and it currently reports no mismatches. A dataset
that says "we checked 200 rows and found two errors" is telling you about its
sample. Without provenance, complete verification is not possible at all, and a
reader disputing one figure has no way to reach the cell behind it.

**What would change it:** nothing at this size. At a hundred million rows the
provenance would have to move to a side table.

## 2. The reporting convention is a column, not a footnote

`period_type` takes one of five values: `calendar_year`, `year_end`,
`fiscal_year`, `fiscal_year_end`, `academic_year`. A fiscal year runs 1 April to
31 March and a fiscal year end refers to 31 March following, both by clause 12 of
the compilers' own notes.

The alternative — and it is what everyone else does — is to put the year in the
year column and mention the convention in prose. Over 60% of the observations
here are dated on a fiscal basis. Merging them into a calendar series produces
something that looks continuous and is wrong by up to a year in places, and
nothing downstream can detect it.

`W05_generalisation.md` records this failure in the wild. The Hitotsubashi
long-term economic series normalised its dates to the Gregorian calendar, and the
fact that six years of one series are fiscal-year figures survives only as a
sentence in a footnote. A machine will not read that.

**The cost** is that a user cannot simply plot `value` against `year`. They have
to decide what to do about the distinction. That is the point.

## 3. A printed zero is not zero

Clause 11 of the compilers' notes gives their own legend: a dash means not
surveyed, an ellipsis means unknown, and a printed `0` means **a quantity below
one unit**. 47 cells are affected, and they carry `flag = less_than_one_unit`
with the value 0.0.

This was got wrong first time round. Treating them as zeros pulls any mean
computed over those series downward, quietly.

**Related, and not fixable here:** the 2006 digitisation converted both the dash
and the ellipsis to a full stop, so the distinction between "not surveyed" and
"unknown" is gone from the spreadsheets and cannot be recovered from them. Both
become `flag = missing`. Anyone who needs the distinction has to go back to the
printed book. This is a loss caused by the digitisation, not by the compilers,
and it is stated plainly rather than papered over.

## 4. Column meanings are written by hand

**Decided twice.** Header reconstruction was automated first. Because a label's
characters are distributed across the columns it spans, they can in principle be
reassembled by following the innermost header's repeat period.

It produced plausible wrong answers. The check used was "are any single-character
labels left?", which passed 12 of 16 tables; inspection showed most of those were
wrong. Two distinct labels had been fused into one, and in one table the title of
the table had been absorbed into a column name. The check was a bad proxy and it
could not see its own failures. `D12_findings.md` has the detail.

Specifications are now written by hand, one per section, 65 of them in
`twstat.corpus1946`. That is slow and it does not scale to the whole compendium
of 634 tables.

**What would change it:** a check that can actually detect a wrong label. Nobody
has one. Until then the labour is the price of not publishing confident nonsense.

## 5. Sections are a first-class column, not an assumption

**Decided twice.** Eleven of the fifty tables stack several tables in one sheet,
each with its own header. The first pipeline found the first dated row and read
to the end of the file, which merged Taiwanese and Japanese populations into
single series in two education tables.

Value-level verification could not catch it. Every number was correct; only its
attribution was wrong. Seven tables already reported complete had to be redone.

Clause 7 of the compilers' notes turns out to describe the practice explicitly:
where categories could not be reconciled across fifty years, the table was cut
into parts and the parts listed separately. The `section` column corresponds to
that editorial act rather than to anything invented here.

**The general lesson** is the one worth keeping: a verification layer can only
find the class of error it is built to find. Checking values will never find a
mis-attribution, and no amount of it should be mistaken for having checked the
dataset.

## 6. Era numerals are not converted arithmetically

The Gregorian year is read from the parenthesised suffix, which 98.2% of
date-like row labels carry.

The reason given for this used to be that conversion would introduce undetectable
errors. `W05_generalisation.md` shows that is false: the conversion agrees with
the printed year on all 117 checkable labels here and all 59 labelled pairs in
the Japanese Imperial Statistical Yearbook index, the 1926 era transition
included.

The real reason is that it would achieve nothing. Only 5.3% of labels name an era
at all, and all but two of those already print the year. Adding a Chinese-numeral
parser would recover almost nothing while enlarging the surface on which the
pipeline can fail quietly.

**The cost is borne by someone else.** On a source that dates rows by era alone,
this parser returns the period and no year. It resolved 0 years out of 33,116
labels in the yearbook index. Whoever reuses it there has to write the
arithmetic, and the documentation now tells them it is safe to.

## 7. Ambiguous cells are flagged, not dropped

`missing`, `less_than_one_unit`, `bracket_artifact`, `non_numeric`. A cell that
cannot be read as a number keeps its row and its provenance rather than
disappearing.

The alternative is a clean file of numbers. The objection to it is that a reader
cannot tell the difference between a figure that was never collected and one that
the pipeline could not parse — and the second is a bug report, which they can
only send if they can see it.

`bracket_artifact` is worth singling out. A figure spanning several printed
columns is set inside a drawn brace which the digitisation kept in the cell. The
pattern for it matched one spelling out of several, and **102 figures in the
published corpus were being discarded as unreadable** until `W06_layout.md`.
They were invisible precisely because a dropped row leaves nothing behind.
Flagged rows can be counted; dropped rows cannot.

## 8. Two verification layers, and only one of them is done

The numeric layer is mechanical and complete: every value re-read from its cell.

The semantic layer — whether `dim1` and `dim2` name what the printed table says
they name — cannot be checked that way. It needs a second person reading the
printed layout independently, and Cohen's kappa between the two.
`twstat.sampling` produces the coding sheets; `validation_plan.md` sets out the
procedure; no second coder has done it.

**The decision was to publish anyway, with the distinction stated in the README,
the codebook and this file.** The alternative was to hold the dataset back until
a second reader could be found, which on present evidence means indefinitely. A
dataset whose limits are stated is more use than one that does not exist, but the
statement has to be prominent rather than buried, and `dim1` and `dim2` are
proposed rather than established until it is done.

## 9. Cross-sectional tables are refused

`header_rows` returns nothing for a section with no dated rows, and the section
is skipped. 151 of the 632 sections in the compendium's other chapters — 23.9% —
are of this kind: a staffing table whose rows are job titles and columns are
departments, at one moment in time.

The schema begins with a year. A snapshot has no place in it, and forcing one in
by inventing a year would be worse than declining. **A quarter of the compendium
cannot be represented by this data model**, which anyone planning to extend the
dataset to the whole book needs to know before they start.

## 10. The source spreadsheets are not redistributed

`raw/` is not in version control. `scripts/download_raw.py` fetches the files
from Academia Sinica, whose digitisation they are.

The compendium itself is a government document and not subject to copyright under
Article 9 of the Copyright Act of the Republic of China, and the figures are
facts. The 2006 digitisation is somebody's work, and the courteous thing is to
point at it rather than mirror it.

**The cost** is that the test suite has to run without the corpus. Tests that
need it are marked `corpus` and skip when `raw/` is absent; the rest build small
spreadsheets in memory. CI runs the second set only.

## 11. None and empty string mean different things in a column specification

In `ColumnSpec`, `dim2=None` means "take this from the innermost header row", and
`dim2=""` means "this column deliberately has no second dimension".

Collapsing them into one falsy value loses the distinction between a column whose
second dimension is to be read from the sheet and a column that genuinely has
none, and the second silently acquires whatever text happens to sit above it.
This was found by comparing a refactor against the previous pipeline's output:
1,881 values had picked up a wrong `dim2`.

It is an unpleasant piece of API design and it is documented at the field rather
than left for someone to discover.
