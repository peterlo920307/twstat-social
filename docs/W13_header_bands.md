# Three health tables were publishing the wrong disease names

Found on 11 September 2026, in a review of the code against the corpus. It is
the most serious defect this project has had, and it had been in the published
dataset since the first complete extraction.

## What was wrong

`Hygiene_Mt487-2`, `Hygiene_Mt488` section 2 and `Hygiene_Mt489` section 2 each
run five or six bands of column headings down a single sheet. Every band re-uses
the same physical columns for a different set of diseases, and every band carries
its own full run of years. Nothing marks the boundaries: no numbered heading, no
blank block, nothing the section detector was looking for.

The pipeline read the first band's headings and applied them to every row down to
the end of the section.

`raw/Hygiene_Mt488.xls` is the clearest case. The section runs from row 37 to row
153 and holds six bands:

```
row  6-7    總計  傷寒  副傷寒  天花  麻疹 …          band 1
row  43     民國二十年(1931)  101306  281  15  3 …   data for band 1
row  59-61  恐水病  破傷風  肺結核  其他結核  梅毒 …   band 2
row  62     民國二十年(1931)  43  43  1310  └──492──┘  data for band 2
row 138-141 其他腎臟、腎盂及輸尿管之疾病 …             band 6
row 142     民國二十年(1931)  └─9118─┘ …             data for band 6
```

Row 62 column 4 holds 1310, a count of pulmonary tuberculosis. It was published
as 副傷寒, paratyphoid — the name that sits in that column in band 1, a hundred
rows above.

**2,976 rows, 8.1% of the dataset, carried a disease name belonging to a
different disease.** Roughly seventy real categories never appeared at all, and
twenty-two names were each reused five or six times for unrelated quantities.

## Why nothing caught it

`twstat verify` re-reads every value from its recorded cell and compares.
Throughout, it reported no mismatches — correctly. Every number was read from
the right cell and transcribed exactly. Only the label was wrong, and a check on
values cannot see a label.

This is the failure `docs/D15_section_bug.md` recorded the day before, written up in
`DESIGN.md` §5 as the general lesson, and demonstrated deliberately in
`EXAMPLE.md` §6. It happened again anyway, in a form the earlier fix did not
cover: D15 was about *numbered* stacking, `1.本省人` / `2.日本人`, and the fix
taught the detector to find numbered markers. These bands are not numbered.

The sampling check could not realistically have caught it either. The coding
sheet drew three cells per section, so about three of Mt488's 1,296 rows, and a
coder would have had to land inside a later band *and* notice.

## The fix

`sections.find` now splits on two things rather than one: a numbered marker, and
a fresh band of column headings interrupting a table that is otherwise
continuous. A band is a row, not itself dated, carrying two or more cells of text
no number can be read out of. One such cell is a unit note; two is a heading.

Run over all fifty files, the band detector fires on exactly the three sections
above and nowhere else. Those three files go from 1, 2 and 2 sections to 5, 7 and
6, and the corpus from 65 specified sections to 78.

## Reading 350 disease names off the sheet

Each new band needed its own column specification. `DESIGN.md` §4 records that
automating header reconstruction produced plausible wrong answers and was
abandoned, so this deserves a word.

That failure was about labels scattered *horizontally* — 「大」 in one column and
「學」 three columns later, where reassembly requires guessing which columns a
label spans. These bands are different. Each column's name is stacked
*vertically* within that one column, across four to six header rows:

```
row 138  輸尿管之
row 139  疾病(因妊
row 140  娠而患者
row 141   除外)
```

There is nothing to guess: the label is that column's own cells, top to bottom.

The method was checked before it was trusted. Assembling band 1 of `Mt487-2` this
way and comparing against the specification a person had already written by hand
gives **21 of 22 columns identical**. The one difference was the section heading
text leaking in from a header row, which is now excluded.

## What the dataset looks like now

|  | before | after |
|---|---|---|
| rows | 36,672 | 36,735 |
| values | 28,667 | 28,745 |
| specified sections | 65 | 78 |
| distinct `dim1` in Mt487-2 / Mt488 / Mt489 | 22 / 22 / 21 | 109 / 119 / 120 |
| keys carrying two different values | 726 | 0 |
| verification mismatches | 0 | 0 |

Two other defects found in the same review are fixed here because they were in
the way of measuring this one:

- A figure printed with the compilers' own footnote marker in front of it,
  `(1)    10`, was rejected as unreadable and its row dropped. 23 figures across
  seven tables. The marker points at a note `data/notes.csv` already carries.
- `Edu_Mt480` gives 共計, 中日文 and 外國文 on the upper header row rather than the
  innermost one, so all three columns published with no second dimension and 117
  rows became indistinguishable triplets. The specification now states them.

## What now protects it

`tests/test_corpus.py` asserts that no `(table_id, section, year, dim1, dim2)`
key carries two different values, and that no source cell is used twice. The
first of those would have failed on 726 keys before this fix. It is a cheap
structural check and it is the one that was missing: the project had a complete
check of values and no check at all of whether two rows were claiming to describe
the same thing.

## A second defect in the same tables, fixed the same day

`Mt487-2` and `Mt489` encode a second dimension in the row stub, pairing each
year across two rows:

```
row 10  '民國  二  十年(1931)┌患者'   17025  762  46 …
row 11  '                   └死亡'    1326  154   4 …
```

Only the first row carried a year, so `extract_file` skipped the second and
**1,895 figures were silently discarded**. The rows that survived were cases only,
and nothing in the schema said so, so a reader taking `Mt487-2 / 傷寒 / 1931 = 762`
had no way to know that 154 deaths existed in the source and had been dropped.

The fix carries the year from the first row of a pair to the rows it joins, and
writes the word after the brace — 患者 or 死亡 — into `dim2`, which these two
tables had deliberately left empty, so the schema does not change. An orphan
`└` row with no opening row above it is not given a year. 39,150 rows and 30,640
values after both fixes; verification still reports no mismatches, and no key
carries two values.
