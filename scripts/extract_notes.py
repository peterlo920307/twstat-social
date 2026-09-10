# -*- coding: utf-8 -*-
"""擷取原表附註欄與材料來源
原書〈編製凡例〉(九)：無法修正之數字問題均於「附註欄」註明。
故附註欄是原編纂者自陳的資料品質紀錄，必須保留。
"""
import re, glob, os, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from sections import find_sections, clean

HEAD = re.compile(r"^\s*(附\s*註|註|材料\s*來源|資料\s*來源|說\s*明|備\s*註|按)\s*[:：(（]?")

def kind(s):
    if re.match(r"^\s*(材料\s*來源|資料\s*來源)", s): return "source"
    if re.match(r"^\s*(附\s*註|註|備\s*註)", s):      return "note"
    return "other"

def extract(path):
    tid = os.path.basename(path).replace(".xls", "")
    df = pd.read_excel(path, header=None)
    secs = find_sections(df)
    def sec_of(r):
        for no, lab, s, e in secs:
            if s <= r < e: return no, (lab or "")
        return 1, ""
    out, i = [], 0
    while i < len(df):
        v = None
        for c in range(min(4, df.shape[1])):
            x = clean(df.iat[i, c])
            if x and HEAD.match(x): v = x; break
        if v:
            # 附註常換行續寫：往下併入不含年份、非新附註的短列
            parts, j = [v], i + 1
            while j < len(df):
                nxt = clean(df.iat[j, 0])
                if not nxt or HEAD.match(nxt) or re.search(r"\(1[89]\d\d\)", nxt): break
                if len(nxt) < 4: break
                parts.append(nxt); j += 1
            no, lab = sec_of(i)
            out.append({"file": tid, "table_id": tid.split("_")[-1],
                        "section": no, "section_label": lab.lstrip("0123456789."),
                        "src_row": i + 1, "type": kind(v),
                        "text": "".join(parts)})
            i = j
        else:
            i += 1
    return out

if __name__ == "__main__":
    rows = []
    for f in sorted(glob.glob("../raw/*.xls")): rows += extract(f)
    d = pd.DataFrame(rows)
    d.to_csv("../data/notes.csv", index=False, encoding="utf-8-sig")
    print(f"data/notes.csv: {len(d)} 條，涵蓋 {d.file.nunique()} 檔")
    print(d.type.value_counts().to_string())
    print(f"平均長度 {d.text.str.len().mean():.0f} 字，最長 {d.text.str.len().max()} 字")
