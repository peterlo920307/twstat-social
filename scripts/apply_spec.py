# -*- coding: utf-8 -*-
"""把 spec_v2.SPEC/DIM2 寫入 header_worksheet_v2.csv 並套用產生 tidy.csv"""
import sys, warnings; warnings.filterwarnings("ignore")
import pandas as pd
from spec_v2 import SPEC, DIM2
ws_csv = "../docs/header_worksheet_v2.csv"
w = pd.read_csv(ws_csv)
w["CORRECT_dim1"] = w["CORRECT_dim1"].astype("object")
w["CORRECT_dim2"] = w["CORRECT_dim2"].astype("object")
n = 0
for (f, sec), segs in SPEC.items():
    for s, e, lab in segs:
        m = (w.file == f) & (w.section == sec) & (w.col >= s) & (w.col <= e)
        w.loc[m, "CORRECT_dim1"] = lab
        w.loc[m, "note"] = "machine-proposed; needs human check"
        n += int(m.sum())
for (f, sec), mp in DIM2.items():
    for c, lab in mp.items():
        w.loc[(w.file == f) & (w.section == sec) & (w.col == c), "CORRECT_dim2"] = lab
w.to_csv(ws_csv, index=False, encoding="utf-8-sig")
print(f"已填 {n} 列 / {len(SPEC)} 個(檔案,區段)")
