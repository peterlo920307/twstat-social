"""Fixtures.

Most tests build small spreadsheets in memory so that the suite runs without the
source corpus, which is not kept in version control. The tests marked ``corpus``
need the real files and are skipped when they are absent.
"""

from pathlib import Path

import pandas as pd
import pytest

RAW = Path(__file__).resolve().parent.parent / "raw"


@pytest.fixture(scope="session")
def raw_dir() -> Path:
    if not RAW.exists() or not list(RAW.glob("*.xls")):
        pytest.skip("source corpus absent; run scripts/download_raw.py")
    return RAW


@pytest.fixture
def stacked_sheet(tmp_path: Path) -> Path:
    """Two tables stacked in one sheet, each with its own two-row header.

    This reproduces the layout that caused Taiwanese and Japanese populations to
    be merged before section detection existed.
    """
    rows = [
        ["表999 兩區段測試", None, None, None],
        [None, None, None, None],
        ["1.本省人", None, None, None],
        [None, "教", None, "員"],
        [None, "共計", "男", "女"],
        ["十 一 年(1922)", 10, 6, 4],
        ["十 二 年(1923)", 12, 7, 5],
        [None, None, None, None],
        ["2.日本人", None, None, None],
        [None, "教", None, "員"],
        [None, "共計", "男", "女"],
        ["十 一 年(1922)", 20, 11, 9],
        ["十 二 年(1923)", 22, 12, 10],
    ]
    path = tmp_path / "Test_Mt999.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path


@pytest.fixture
def annotated_sheet(tmp_path: Path) -> Path:
    """A sheet whose footnotes exercise every branch of note extraction.

    The first note runs onto a second line, the second is short enough to be a
    heading rather than a continuation, and the third is a source attribution.
    """
    rows = [
        ["表996 附註測試", None],
        ["1.第一區段", None],
        [None, "學生數"],
        ["十 一 年(1922)", 5],
        ["附註:(1)第一行說明", None],
        ["接續的第二行說明文字", None],
        ["2.第二區段", None],
        [None, "學生數"],
        ["十 二 年(1923)", 7],
        ["註:短註", None],
        ["材料來源:測試資料", None],
    ]
    path = tmp_path / "Test_Mt996.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path


@pytest.fixture
def flat_sheet(tmp_path: Path) -> Path:
    """One table, one header row, including each missing-value marker."""
    rows = [
        ["表998 單區段測試", None, None],
        [None, "校數", "學生數"],
        ["十 一 年(1922)", 3, 100],
        ["十 二 年(1923)", ".", 0],
        ["十 三 年(1924)", "└─7─┘", 120],
        ["材料來源:測試用", None, None],
    ]
    path = tmp_path / "Test_Mt998.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path
