# -*- coding: utf-8 -*-
"""Download the 50 source .xls files from Academia Sinica.

The raw files are NOT redistributed in this repository. They are produced and
hosted by the Institute of Information Science, Academia Sinica, which digitised
the 1946 compendium in 2006. Run this script once to reproduce `raw/`.

    python scripts/download_raw.py

Source: http://twstudy.iis.sinica.edu.tw/twstatistic50/
"""
import json, os, time, urllib.parse, urllib.request

BASE = "http://twstudy.iis.sinica.edu.tw/twstatistic50/"
SECTIONS = ["Edu", "Hygiene", "Welfare"]          # the three chapters used here
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "docs", "twstat50_tables.json")
OUT = os.path.join(ROOT, "raw")

def main():
    tables = json.load(open(INDEX, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    ok = skip = fail = 0
    for sec in SECTIONS:
        for t in tables[sec]:
            dest = os.path.join(OUT, f"{sec}_{os.path.basename(t['file'])}")
            if os.path.exists(dest):
                skip += 1; continue
            url = BASE + urllib.parse.quote(t["file"])
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "twstat-social/0.1"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    open(dest, "wb").write(r.read())
                ok += 1
                print(f"  {os.path.basename(dest)}")
            except Exception as e:
                fail += 1
                print(f"  FAILED {os.path.basename(dest)}: {e}")
            time.sleep(0.25)
    print(f"\ndownloaded {ok}, already present {skip}, failed {fail}")
    if fail:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
