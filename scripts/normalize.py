# -*- coding: utf-8 -*-
"""《臺灣省五十一年來統計提要》紀年與缺值正規化
實測：50 檔、2,440 個年份/註記標記，自動解出率 91.0%
"""
import re

NOTE_RE = re.compile(r"^\s*(材料\s*來源|資料\s*來源|附\s*註|說\s*明|註)\s*[:：]?")
YEAR_RE = re.compile(r"\((1[89]\d\d)\)")

def norm_year(s):
    """(year:int|None, period_type:str|None, is_note:bool)

    period_type 語意（**不可合併**，實測分布見下）：
      fiscal_year_end 年度底 850 | calendar_year 年 814
      year_end 年底 490        | fiscal_year 年度 67
    """
    if s is None: return (None, None, False)
    t = str(s).strip()
    if not t or t == "nan": return (None, None, False)
    if NOTE_RE.match(t): return (None, None, True)
    m = YEAR_RE.search(t)
    yr = int(m.group(1)) if m else None
    if   re.search(r"年\s*度\s*底", t): pt = "fiscal_year_end"
    elif re.search(r"年\s*度",     t): pt = "fiscal_year"
    elif re.search(r"年\s*底",     t): pt = "year_end"
    elif re.search(r"年",          t): pt = "calendar_year"
    else: pt = None
    return (yr, pt, False)

# 依原書〈編製凡例〉(十一)：
#   「－」未調查或無數字 ｜「…」數字不明 ｜「0」有數不及一單位（非零）
# ⚠️ 中研院 2006 年數位化時已將「－」與「…」一併轉為「.」，兩者語意無法還原。
MISSING = {".", "．", "…", "-", "―", "─", "‥", ""}

def norm_value(v):
    """(value:float|None, flag:str|None)
    flag: 'missing_dot' 原表以「.」表示缺值（48/50 檔）
          'bracket_artifact' └─N─┘ 跨欄合併標記（10/50 檔）
    """
    if v is None: return (None, None)
    s = str(v).strip()
    if s in MISSING or s.lower() == "nan": return (None, "missing_dot")
    m = re.match(r"^└─\s*([\d,\.]+)\s*─┘$", s)
    if m:
        try: return (float(m.group(1).replace(",", "")), "bracket_artifact")
        except ValueError: return (None, "bracket_artifact")
    s2 = s.replace(",", "").replace(" ", "")
    try:
        f = float(s2)
    except ValueError:
        return (None, "non_numeric")
    # 原書凡例(十一)：「0」表示「有數不及一單位」，非真正的零
    if f == 0:
        return (0.0, "less_than_one_unit")
    return (f, None)
