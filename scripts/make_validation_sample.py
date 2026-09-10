# -*- coding: utf-8 -*-
"""產生人工驗證抽樣表與 Cohen's κ 計算

設計要點（見 docs/validation_plan.md）：
  第一層「數值轉錄正確性」可對照 src_row/src_col 自動全檢，不需抽樣、不需人工。
  第二層「維度語意標註」才需要兩位人類獨立編碼者 → 本腳本處理第二層。
"""
import argparse, glob, os
import pandas as pd
from normalize import norm_value

def auto_verify(tidy_csv, xls_dir):
    """第一層：數值 100% 自動回檢（不抽樣）"""
    t = pd.read_csv(tidy_csv)
    bad = []
    for tid, g in t.groupby("table_id"):
        cand = glob.glob(os.path.join(xls_dir, f"*{tid}.xls"))
        if not cand: continue
        src = pd.read_excel(cand[0], header=None)
        for _, r in g.iterrows():
            if pd.isna(r["value"]): continue
            try: raw = src.iat[int(r["src_row"]) - 1, int(r["src_col"]) - 1]
            except Exception: bad.append((tid, r["src_row"], r["src_col"], "out_of_range")); continue
            # 必須套用與管線相同的解析規則（含 └─N─┘ 偽影），否則會誤報
            ref, _ = norm_value(raw)
            if ref is None:
                bad.append((tid, r["src_row"], r["src_col"], f"unparsable:{raw}"))
            elif abs(ref - float(r["value"])) > 1e-9:
                bad.append((tid, r["src_row"], r["src_col"], f"{raw}!={r['value']}"))
    return bad

def draw_sample(tidy_csv, n=200, seed=20260909):
    """第二層：分層抽樣，產生空白編碼表供兩位標註者各自填寫"""
    t = pd.read_csv(tidy_csv)
    t = t[t["dim1"].notna()]
    per = max(1, n // max(1, t["table_id"].nunique()))
    s = (t.groupby("table_id", group_keys=False)
           .apply(lambda g: g.sample(min(len(g), per), random_state=seed)))
    if len(s) > n: s = s.sample(n, random_state=seed)
    out = s[["table_id", "src_row", "src_col", "year", "value"]].copy()
    out["coder_dim1"] = ""      # 標註者填寫
    out["coder_dim2"] = ""
    out["note"] = ""
    return out.sort_values(["table_id", "src_row", "src_col"]).reset_index(drop=True)

def kappa(a, b):
    """Cohen's κ（未加權）"""
    a, b = list(a), list(b)
    n = len(a); cats = sorted(set(a) | set(b))
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("tidy_csv"); p.add_argument("--n", type=int, default=200)
    p.add_argument("--out", default="validation_sheet.csv")
    a = p.parse_args()
    df = draw_sample(a.tidy_csv, a.n)
    df.to_csv(a.out, index=False, encoding="utf-8-sig")
    print(f"已產生 {len(df)} 筆抽樣，涵蓋 {df.table_id.nunique()} 張表 -> {a.out}")
    print("請複製兩份，由兩位標註者各自獨立填寫 coder_dim1 / coder_dim2，勿互相參照。")
