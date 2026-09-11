# Testing the era-date parser on corpora it was not written for

Everything in this file can be reproduced with

    python scripts/second_corpus.py <scratch-directory> raw

which downloads the two external corpora, runs the parser over them, and prints
the numbers quoted below. Neither external corpus is redistributed here.

## Why this was worth doing

`twstat.eradate` was written against one publication. A parser written against
one publication tends to encode that publication's habits without anyone
noticing, because every test it passes is drawn from the same source. The only
way to find out which parts are general is to run it on something else.

Two corpora were used, both published by the Institute of Economic Research,
Hitotsubashi University:

- **LTES** — *Estimates of Long-Term Economic Statistics of Japan since 1868*.
  Eight workbooks covering volumes 1 to 5, 290 sheets.
- **The Imperial Statistical Yearbook index**, 1882–1940. 33,116 table titles,
  each row also carrying the Gregorian year, which makes it a labelled test set
  rather than just a pile of unseen strings.

## What held up

The period taxonomy did. Of the 20,419 era expressions embedded in the yearbook
titles, the parser assigned a period type to every one: 15,311 calendar years and
5,108 fiscal years. The 年 / 年度 distinction that this package exists to preserve
is not a quirk of the 1946 compendium. It is how this yearbook dated its tables
across 1882–1940, and a reader who merges the two is making the same
mistake in either corpus.

That the yearbook is a third of a century older than the compendium, produced by
a different government for a different country, and typeset by different hands,
is what makes this worth stating.

## What did not

The Gregorian year. The parser resolved **0 years out of 33,116 titles**, because
it reads the year out of a parenthesised suffix and this corpus never prints one.

This is not a bug that can be fixed by widening a regular expression. It is the
consequence of a design decision, and the measurements below show that the
decision was right for the wrong reason.

## The reason for that decision was wrong

`parse()` used to say that era numerals are not converted arithmetically because
doing so "would introduce errors that no downstream check could detect". The
yearbook index disproves that. It supplies 59 era/Gregorian pairs, none of them
ambiguous, and the obvious arithmetic — 明治 N = 1867 + N, 大正 N = 1911 + N,
昭和 N = 1925 + N — agrees with the printed year **59 times out of 59**,
including 大正15年・昭和元年, the transition year that looks like it should break.

The same check inside the 1946 compendium agrees **117 times out of 117** on
民國前 N = 1912 − N and 民國 N = 1911 + N.

So arithmetic conversion is not dangerous. It is merely useless *here*, and the
docstring now says so: only 5.3% of date-like row labels in the compendium name
an era at all, and all but two of those already carry the printed year. Adding a
Chinese-numeral parser would recover almost nothing and would enlarge the
surface on which the pipeline can fail quietly.

The distinction matters because a reader deciding whether to reuse this code on a
source that *does* date its rows by era alone needs to know that conversion is
available to them, not that it is forbidden.

## A fact about the compendium that the docstring had wrong

The module used to describe its corpus as labelling rows with "a mixture of
Japanese and Republican era years". All 45,691 non-blank cells were checked.
**Not one names a Japanese era.**

The 1946 compilers re-dated fifty years of colonial statistics into Republican
reckoning throughout, writing pre-1912 years as 民國前 N, and appended the
Gregorian year in parentheses on 98.2% of date-like row labels. Every table of
Japanese-era figures was silently converted before it was printed.

That is an editorial act by an incoming administration, performed on every page,
and it is invisible in the tidy data unless someone says so. It is now recorded
here and in `docs/bias_statement.md`.

## LTES, and why a modern re-publication is the wrong kind of test

LTES contains 4,156 distinct short labels across its 290 sheets and **not one of
them names an era**. Its editors normalised every date to the Gregorian calendar
before publishing.

That makes it useless for testing an era parser, but it is instructive for a
different reason. The fiscal-year distinction did not survive normalisation as
data. It survives as prose, in footnotes such as
「注　*は推計なし。1946～1951年は会計年度。」 — six years of the series are dated
differently from the rest, and the only record of it is a sentence a machine will
not read.

This is the failure this package is built to avoid, found in the wild in a
standard scholarly source.

## What is now pinned by tests

`tests/test_eradate.py` carries the yearbook labels verbatim. They assert that
the period type is recognised and that no year is invented. If someone later adds
era arithmetic, those tests are where they will have to say so deliberately.

## What this does not tell us

Only `eradate` was tested here. `sections` and `values` encode assumptions about
typesetting that these corpora cannot exercise, because neither is a scan of a
printed table with stacked sections and scattered-character headers. That is W06,
and it uses the 599 tables of the compendium's other 21 chapters, which this
package has never seen.
