# The investigation record

Everything here was written while the work was being done, and nothing has been
tidied up afterwards. Several entries record decisions that turned out to be
wrong or directions that were abandoned; they are kept because the reason a
dataset looks the way it does is usually a sequence of things that did not work.

Two practical notes. The `D` and `T` numbering is not contiguous — the numbers
come from a task list, and tasks that produced nothing left no file. And the
notes written during the investigation are in Chinese, because the sources are;
the documents written for readers of the finished work are in English.

## Start here

| | |
|---|---|
| [`../README.md`](../README.md) | What the package does, what carries over to another source, and what went wrong |
| [`CODEBOOK.md`](CODEBOOK.md) | Every column of `data/tidy.csv`, its type, and what its values mean |
| [`WORK.md`](WORK.md) | What is still open |

## How the dataset was built

In order. Each entry is the record of one working session.

| | |
|---|---|
| [`D08_findings.md`](D08_findings.md) | Downloading 50 spreadsheets and finding out what is actually in them |
| [`D09_findings.md`](D09_findings.md) | Era years and missing values: the first normalisation, and one substantive finding |
| [`D10_findings.md`](D10_findings.md) | The tidy schema, a working prototype, and the limits it exposed |
| [`D12_findings.md`](D12_findings.md) | **Automated header reconstruction failed.** A proxy check passed 12 of 16 tables that inspection showed were wrong |
| [`D13_progress.md`](D13_progress.md), [`D14_education_v01.md`](D14_education_v01.md) | The education chapter, first complete version |
| [`D15_section_bug.md`](D15_section_bug.md) | **Stacked sections went undetected.** Seven tables already reported complete had to be redone |
| [`D16_progress.md`](D16_progress.md), [`D17_progress.md`](D17_progress.md), [`D18_complete.md`](D18_complete.md) | Rework after the section fix, then health, then all 48 tables |

## Testing the code on material it had not seen

| | |
|---|---|
| [`W05_generalisation.md`](W05_generalisation.md) | The era parser against two external corpora. The period taxonomy carries over; resolving the Gregorian year does not. Two claims the module made about itself were false |
| [`W06_layout.md`](W06_layout.md) | Section detection and cell interpretation against the compendium's other 582 tables. Two bugs, one of which was discarding 102 figures from the published corpus |

Both are reproduced by `scripts/second_corpus.py` and `scripts/holdout.py`.

## The source, and what it does not say

| | |
|---|---|
| [`D19_preface.md`](D19_preface.md) | The compilers' own preface and compilation notes. It answered most of the open questions below, including what a printed `0` means |
| [`D20_notes.md`](D20_notes.md) | The 102 footnotes and source attributions recovered into `data/notes.csv`, including the one that settles how indigenous children were counted |
| [`bias_statement.md`](bias_statement.md) | What the data cannot support: the 1895–96 blank, the 1943 collapse, who was excluded, and the fact that the whole run was re-dated into Republican reckoning |

## What is not verified, and how it would be

| | |
|---|---|
| [`validation_plan.md`](validation_plan.md) | The two-coder procedure and Cohen's kappa for checking `dim1` and `dim2`. Not yet carried out |

## Publication

| | |
|---|---|
| [`JOHD_draft.md`](JOHD_draft.md) | Draft data paper against the journal's template. Still has open placeholders |
| [`T44_findings.md`](T44_findings.md) | Article processing charges and alternative venues |
| [`T46_findings.md`](T46_findings.md) | Submission-to-publication timelines |
| [`zenodo_workflow.md`](zenodo_workflow.md) | Depositing and obtaining a DOI |

## Directions that were investigated and dropped

Kept because the case for the direction that was chosen rests on them.

| | |
|---|---|
| [`T01`](T01_findings.md), [`T02`](T02_findings.md), [`T03`](T03_findings.md), [`T04`](T04_findings.md), [`T05`](T05_findings.md), [`T08`](T08_findings.md), [`T09`](T09_findings.md) | The Provincial Assembly archive: search interface, record structure, CSV export, member biographies |
| [`T06_findings.md`](T06_findings.md), [`T07_findings.md`](T07_findings.md) | Copyright and reuse terms for that archive. Unresolved, and the risk rose rather than fell |
| [`T10_findings.md`](T10_findings.md), [`T11_findings.md`](T11_findings.md) | **Why it was dropped.** The novelty audit and the discovery that NTU's digital humanities centre already holds the ground |
| [`D06_findings.md`](D06_findings.md) | **The equivalent audit for this direction.** NTU economics has already digitised a great deal of colonial statistics |
| [`D07_findings.md`](D07_findings.md) | Why a gap remains anyway: education, health and relief were of no use to economists, so nobody digitised them |
| [`D01_findings.md`](D01_findings.md), [`D02_findings.md`](D02_findings.md) | Earlier attempts at the colonial statistical archives, partly blocked |
| [`D11_findings.md`](D11_findings.md) | Finding the Academia Sinica digitisation, which is what made the whole thing possible |

## The original plan

[`TASKS.md`](TASKS.md) is the fifty-item list the `T` and `D` numbers refer to,
with each item marked done, dropped or stuck. It is the quickest way to see what
was tried and what was refused.
