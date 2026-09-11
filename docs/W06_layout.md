# Testing section detection and cell interpretation on unseen tables

Reproduce with

    python scripts/holdout.py <scratch-directory>

which downloads the tables and prints every number below. The files are not
redistributed here.

## The test set

The published dataset uses 48 of the 50 tables in three chapters of the 1946
compendium: education, hygiene, welfare. The other two are cross-sectional and
are excluded. The compendium has 24 chapters and 634 tables. The
other 21 chapters — administration, agriculture, banking, climate, commerce,
finance, fishing, forestry, animal husbandry, industry, justice, labour, land,
mining, monopoly, police, population, post, railways, roads, shipping — were
downloaded and run through `sections` and `values` without being looked at first.

**599 files, 649 sections, 473,293 non-blank cells.** That is ten times the
cells the code was written against, typeset by the same compilers for subjects I
have not read.

`eradate` was tested separately, against two external corpora; see
`docs/W05_generalisation.md`.

## Two bugs, both of the kind that does not announce itself

### Full-width full stops defeated section detection

A stacked table is marked `1.本省人`, `2.日本人`. The detector required an ASCII
period. The compendium also uses the full-width U+FF0E, `１．官等`, and in print
the two are the same character.

**117 markers across 102 of the 599 files went unread.** The count and the
damage are different numbers, and it is worth being precise. In 96 of those files
the missed marker was the only one, so it moved where the section began rather
than merging anything. **In the other 6 it merged two sections into one**: every
figure correct, every attribution wrong. That is the failure recorded in
`docs/D15_section_bug.md`, which merged Taiwanese and Japanese populations into a
single series, and it is just as invisible — no value is wrong, so no check on
values can find it.

Not one of the 102 files is in the three chapters used for the published dataset,
which is the whole reason it survived. `_MARKER` now accepts either stop, and the
count of missed markers across all 599 files is 0.

### The brace pattern matched one spelling out of several

A figure that spans several printed columns is set inside a drawn brace, and the
2006 digitisation kept the brace inside the cell. The pattern matched `└─42─┘`.
The compilers also wrote `┌─1─┐`, `└──126──┘`, `┌────298────┐`,
`└───────76───────┘`, `└────────────────────385────────────────────┘`, and forms
with a single corner on one side such as `┐4.61` and `├5421.4627`. All of those
were being discarded as unreadable.

**This one is not confined to the unseen chapters. 98 figures in the published
corpus were being thrown away.** `data/tidy.csv` goes from 36,570 to 36,672 rows
— 102 more rows, of which 98 carry a number and the rest are braced missing
markers. No existing value changed; the fix only recovers.

Two cases the widened pattern must refuse, and does:

- `└32.12.22` is a date, 民國32年12月22日, not a number with two decimal points.
- `181─365日` is a range of days, using the rule character as a dash.

And one it must treat as neither: `└─.─┘` is the compilers' missing marker inside
a brace. It now reads as missing rather than unreadable, which keeps its row in
the output instead of dropping it.

## What held up

**Section detection, once the stop was fixed.** 649 sections across 599 files, no
markers missed.

**The missing-value legend.** The proportions are close enough to those in the
three chapters the code was written against that nothing looks out of place:
69.4% numbers against 74.3%, 24.0% missing against 18.4%, 6.5% non-numeric
against 6.9%. The unseen chapters are
slightly sparser, which is what one would expect of subjects that were surveyed
less often than schools and hospitals.

**Refusing cross-sectional tables.** 152 of the 649 sections (23.4%) have no
dated row and `header_rows` returns `(None, [])` for them. That is correct
behaviour, not a failure: `表100 臺灣省行政長官公署法定員額` is a snapshot of
one point in time, rows are job titles and columns are departments, and it has no
place in a schema whose first column is a year. It is worth knowing that a
quarter of the compendium is shaped this way before anyone plans to extend the
dataset to the whole book.

## Columns that hold typography, not data

Some columns hold no data at all. They hold printed typography that the
digitisation preserved as cells:

- `+` — 231 cells. In `Bank_Mt383` an entire column is the plus sign printed
  between two addends.
- `│` — 181 cells, a vertical rule.
- Corner characters — about 97 more.

`values` classifies all of these as non-numeric, which is right, but nothing in
the pipeline warns a person writing a column specification that column 12 of
`Bank_Mt383` is not a variable. Since specifications are written by hand against
the sheet, a human has a chance of noticing — though nothing forces them to, and
no check would catch it if they did not. It is recorded here so that whoever
writes specifications for the remaining tables knows to expect it.

## Why section handling looks more general than it is

**11 of the 50 tables here are stacked (22%). Only 20 of the other 599 are
(3.3%).**

Education, hygiene and welfare are unusually complicated. Their categories were
reorganised repeatedly across fifty years — schools were renamed and merged,
disease classifications were revised — and clause 7 of the compilers' notes says
that where categories could not be reconciled they were 「割為數段分列之」, cut
into parts and listed separately.

So the three chapters that first motivated section handling are the three that
need it most. That is a fair description of how this code came to exist, and it
should temper any claim that the section machinery is generally necessary. On
most of the compendium it does nothing.
