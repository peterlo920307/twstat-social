"""Download the 50 source .xls files from Academia Sinica.

The raw files are NOT redistributed in this repository. They are produced and
hosted by the Institute of Information Science, Academia Sinica, which digitised
the 1946 compendium in 2006. Run this script once to reproduce `raw/`.

    python scripts/download_raw.py

Every file is checked against ``docs/raw_manifest.json``, which records the
SHA-256 and size of each file in the author's own ``raw/``, the copy that
``data/tidy.csv`` was extracted from and verified against. A file that is
already on disk and matches is left alone; anything else is fetched again. A
download that is a real spreadsheet but does not match is kept, reported, and
makes the script exit non-zero: the source may have been re-issued since, and
extracting from it will not reproduce the published data.

Source: https://twstudy.iis.sinica.edu.tw/TwStatistic50/
"""

import hashlib
import json
import os
import time
import urllib.parse

import _fetch  # scripts/_fetch.py

# The address the server redirects every older form of the URL to. The host
# does not care about case: EDU/Mt468.xls is answered from EDU/MT468.XLS.
BASE = "https://twstudy.iis.sinica.edu.tw/TwStatistic50/"
SECTIONS = ["Edu", "Hygiene", "Welfare"]  # the three chapters used here
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "docs", "twstat50_tables.json")
MANIFEST = os.path.join(ROOT, "docs", "raw_manifest.json")
OUT = os.path.join(ROOT, "raw")

# Seconds between requests. The host is a small academic server behind a
# firewall; fifty files a second apart is under two minutes and a load nobody
# will notice.
PAUSE = 1.0


def fingerprint(payload):
    """Return the manifest entry that ``payload`` would have."""
    return {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def matches(path, expected):
    """Say whether the file at ``path`` is the one the manifest describes."""
    try:
        if os.path.getsize(path) != expected["bytes"]:
            return False
        with open(path, "rb") as handle:
            return fingerprint(handle.read()) == expected
    except OSError:
        return False


def main():
    """Fetch every table of the three chapters into ``raw/``.

    Returns:
        0 if every file is present and matches the manifest, otherwise 1.
    """
    _fetch.utf8_console()
    with open(INDEX, encoding="utf-8") as handle:
        tables = json.load(handle)
    with open(MANIFEST, encoding="utf-8") as handle:
        manifest = json.load(handle)
    wanted = [
        (f"{sec}_{os.path.basename(t['file'])}", BASE + urllib.parse.quote(t["file"]))
        for sec in SECTIONS
        for t in tables[sec]
    ]
    unlisted = [name for name, _ in wanted if name not in manifest]
    if unlisted:
        # The index and the manifest have drifted apart, so nothing downloaded
        # could be checked. Stop before asking the server for anything.
        raise SystemExit(f"{MANIFEST} has no entry for: {', '.join(unlisted)}")
    _fetch.require_writable(OUT)

    ok = skip = 0
    failed, mismatched = [], []
    for name, url in wanted:
        dest = os.path.join(OUT, name)
        expected = manifest[name]
        if matches(dest, expected):
            skip += 1
            continue
        if os.path.exists(dest):
            # Most likely a truncated file or an error page left by an earlier
            # version of this script, which wrote whatever the server sent.
            print(f"  {name} is on disk but does not match the manifest; fetching it again")
        try:
            payload = _fetch.download(url, dest, timeout=90)
        except _fetch.FetchError as error:
            failed.append(name)
            print(f"  FAILED {name}: {error}")
        else:
            got = fingerprint(payload)
            if got == expected:
                ok += 1
                print(f"  {name}")
            else:
                mismatched.append(name)
                print(
                    f"  MISMATCH {name}: {got['bytes']} bytes, sha256 {got['sha256'][:16]}...;"
                    f" the manifest has {expected['bytes']} bytes,"
                    f" sha256 {expected['sha256'][:16]}..."
                )
        time.sleep(PAUSE)

    print(
        f"\ndownloaded {ok}, already present {skip}, failed {len(failed)},"
        f" present but not matching the manifest {len(mismatched)}"
    )
    if failed:
        print("\nnot downloaded:")
        for name in failed:
            print(f"  {name}")
    if mismatched:
        print(
            "\npresent but does not match the manifest — the source may have been re-issued."
            "\nExtracting from these will not reproduce data/tidy.csv:"
        )
        for name in mismatched:
            print(f"  {name}")
    return 1 if failed or mismatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
