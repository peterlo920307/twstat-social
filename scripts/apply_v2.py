# -*- coding: utf-8 -*-
"""區段感知的套用器：讀入 header_worksheet_v2.csv 產生 data/tidy.csv
只處理 CORRECT_dim1 已填寫的 (檔案,區段)，未填者跳過並列出。
"""
import sys, os, glob, collections, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from normalize import norm_year, norm_value
from sections import find_sections, section_header

def load(ws_csv):
    ws = pd.read_csv(ws_csv)
    ws = ws[ws["CORRECT_dim1"].notna() & (ws["CORRECT_dim1"].astype(str).str.strip() != "")]
    ov = collections.defaultdict(dict)
    for _, r in ws.iterrows():
        if pd.isna(r["col"]): continue
        ov[(str(r["file"]), int(r["section"]))][int(r["col"])] = (
            str(r["CORRECT_dim1"]).strip(),
            str(r.get("CORRECT_dim2", "") or "").strip(),
            str(r.get("section_label", "") or "").strip())
    return ov

def build(path, tid, ov):
    df = pd.read_excel(path, header=None)
    recs = []
    for no, lab, s, e in find_sections(df):
        colmap = ov.get((tid, no))
        if not colmap: continue
        first, _ = section_header(df, s, e)
        if first is None: continue
        for i in range(first, e):
            y, pt, isnote = norm_year(df.iat[i, 0])
            if isnote or not y: continue
            for c1, (d1, d2, slab) in colmap.items():
                c = c1 - 1
                if c >= df.shape[1]: continue
                val, flag = norm_value(df.iat[i, c])
                if val is None and flag in (None, "non_numeric"): continue
                recs.append({"table_id": tid.split("_")[-1], "section": no,
                             "section_label": (slab or lab or "").lstrip("0123456789."),
                             "year": y, "period_type": pt, "dim1": d1, "dim2": d2 or None,
                             "value": val, "flag": flag, "src_row": i + 1, "src_col": c1})
    return pd.DataFrame(recs)

if __name__ == "__main__":
    ws_csv, raw_dir, out_csv = sys.argv[1], sys.argv[2], sys.argv[3]
    ov = load(ws_csv)
    frames, done, skipped = [], set(), []
    for p in sorted(glob.glob(os.path.join(raw_dir, "*.xls"))):
        tid = os.path.basename(p).replace(".xls", "")
        if not any(k[0] == tid for k in ov): skipped.append(tid); continue
        t = build(p, tid, ov)
        if len(t): frames.append(t); done.add(tid)
    if not frames:
        print("尚無已填寫的區段。"); sys.exit(0)
    out = pd.concat(frames, ignore_index=True)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"{out_csv}: {len(out):,} 列 / {len(done)} 表 / "
          f"{out.groupby(['table_id','section']).ngroups} 區段")
    print(f"有效數值 {out['value'].notna().sum():,}")
    if skipped: print(f"待填 {len(skipped)} 表")
