# -*- coding: utf-8 -*-
"""產生區段感知的表頭工作表（取代舊版 header_worksheet.csv）"""
import glob, os, csv, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from sections import find_sections, section_header, clean

def build(raw_dir, out_csv):
    rows = []
    for f in sorted(glob.glob(os.path.join(raw_dir, "*.xls"))):
        tid = os.path.basename(f).replace(".xls", "")
        df = pd.read_excel(f, header=None)
        for no, lab, s, e in find_sections(df):
            first, hdr = section_header(df, s, e)
            if first is None:
                rows.append({"file": tid, "section": no, "section_label": lab or "",
                             "col": "", "bottom_label": "", "upper_fragments": "",
                             "CORRECT_dim1": "", "CORRECT_dim2": "",
                             "note": "no year rows — needs separate schema"})
                continue
            if not hdr: continue
            bot = hdr[-1]
            for c in range(1, df.shape[1]):
                bl = clean(df.iat[bot, c])
                ups = [clean(df.iat[r, c]) for r in hdr[:-1]]
                ups = [u for u in ups if u]
                if not bl and not ups: continue
                rows.append({"file": tid, "section": no, "section_label": lab or "",
                             "col": c + 1, "bottom_label": bl or "",
                             "upper_fragments": "／".join(ups),
                             "CORRECT_dim1": "", "CORRECT_dim2": bl or "", "note": ""})
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "section", "section_label", "col",
                                           "bottom_label", "upper_fragments",
                                           "CORRECT_dim1", "CORRECT_dim2", "note"])
        w.writeheader(); w.writerows(rows)
    return rows

if __name__ == "__main__":
    import sys
    rows = build(sys.argv[1], sys.argv[2])
    df = pd.DataFrame(rows)
    print(f"已產生 {sys.argv[2]}：{len(rows)} 列")
    print(f"檔案 {df.file.nunique()} 個，(檔案,區段) 組合 {df.groupby(['file','section']).ngroups} 組")
