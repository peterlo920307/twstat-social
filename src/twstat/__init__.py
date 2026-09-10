"""Tools for recovering tidy data from legacy East Asian statistical tables.

The corpus this was built for is the *Taiwan Province Statistical Abstract for
the Past Fifty-One Years* (1946), digitised by Academia Sinica in 2006 as a set
of Excel files that preserve the printed layout and little else.

Typical use::

    from twstat import extract_corpus, verify
    from twstat.spec import SpecBook

    book = SpecBook()
    book.define("Edu_Mt468", 1, [(2, 4, "大學"), (5, 7, "專門學校")])

    tidy = extract_corpus("raw", book)
    assert verify(tidy, "raw") == []
"""

from .eradate import EraDate, Period
from .eradate import parse as parse_date
from .extract import Observation, extract_corpus, extract_file
from .notes import Note, extract_notes
from .sampling import coding_sheet, cohen_kappa
from .sections import Section
from .sections import find as find_sections
from .spec import ColumnSpec, SectionSpec, SpecBook
from .values import Flag, Value
from .values import parse as parse_value
from .verify import Mismatch, SourceNotFoundError, verify

__version__ = "0.1.0"

__all__ = [
    "ColumnSpec",
    "EraDate",
    "Flag",
    "Mismatch",
    "Note",
    "Observation",
    "Period",
    "Section",
    "SectionSpec",
    "SourceNotFoundError",
    "SpecBook",
    "Value",
    "__version__",
    "coding_sheet",
    "cohen_kappa",
    "extract_corpus",
    "extract_file",
    "extract_notes",
    "find_sections",
    "parse_date",
    "parse_value",
    "verify",
]
