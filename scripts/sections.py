# -*- coding: utf-8 -*-
"""區段偵測：原表常將多個機構／族群／期間垂直堆疊於同一檔，
各區段有獨立表頭，欄位配置甚至可能位移。
未區分區段會把不同對象的數字混成同一條序列（語意錯誤，auto_verify 抓不到）。
"""
import re
import pandas as pd
from normalize import norm_year

SEC_RE = re.compile(r"^\d+\.[^\d]")

def clean(v):
    if v is None or str(v) == "nan": return None
    s = re.sub(r"\s+", "", str(v)).strip()
    return s or None

def find_sections(df, max_scan_cols=5):
    """回傳 [(sec_no, label, start_row, end_row)]，row 為 0-based、end 為排他"""
    marks = []
    for r in range(len(df)):
        for c in range(min(max_scan_cols, df.shape[1])):
            v = clean(df.iat[r, c])
            if v and SEC_RE.match(v) and len(v) < 40:
                marks.append((r, v)); break
    if not marks:
        return [(1, None, 0, len(df))]
    out = []
    for i, (r, lab) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(df)
        out.append((i + 1, lab, r, end))
    return out

def section_header(df, start, end):
    """回傳 (資料起始列, 表頭列索引清單) —— 皆為該區段內的絕對列號"""
    first = None
    for i in range(start, end):
        if norm_year(df.iat[i, 0])[0]: first = i; break
    if first is None: return None, []
    hdr = [r for r in range(start, first)
           if any(clean(df.iat[r, c]) for c in range(1, df.shape[1]))]
    hdr = [r for r in hdr
           if not (clean(df.iat[r, 0]) or "").startswith("表")
           and not SEC_RE.match(clean(df.iat[r, 0]) or "")]
    return first, hdr

def profile(path):
    """列出一個檔案的所有區段與其表頭／年份範圍"""
    df = pd.read_excel(path, header=None)
    rows = []
    for no, lab, s, e in find_sections(df):
        first, hdr = section_header(df, s, e)
        yrs = [norm_year(df.iat[k, 0])[0] for k in range(first, e)] if first else []
        yrs = [y for y in yrs if y]
        rows.append({"section": no, "label": lab, "start": s + 1, "end": e,
                     "data_from": (first + 1) if first else None,
                     "header_rows": [h + 1 for h in hdr],
                     "ymin": min(yrs) if yrs else None,
                     "ymax": max(yrs) if yrs else None, "n_years": len(yrs)})
    return df, rows
