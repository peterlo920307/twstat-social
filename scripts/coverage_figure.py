"""Draw how many tables report each year, by chapter, from data/tidy.csv.

    python scripts/coverage_figure.py

Writes docs/figures/coverage.svg, coverage-dark.svg and coverage.csv. The CSV is
the same counts as a table, for anyone who cannot tell the colours apart or
wants the numbers. The SVG is written by hand rather than through a plotting
library so that the output is small, byte-for-byte reproducible, and readable
as text in a diff.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from twstat.corpus1946 import build  # noqa: E402

OUT = ROOT / "docs" / "figures"
FIRST, LAST = 1895, 1945

# Chapter prefixes of the source file names, bottom of the stack first.
CHAPTERS = [("Edu", "Education"), ("Hygiene", "Hygiene"), ("Welfare", "Welfare")]

# The first three categorical slots, which hold apart for every pair in both
# modes. Dark mode uses the same hues stepped for the dark surface.
THEMES = {
    "light": {
        "surface": "#fcfcfb",
        "primary": "#0b0b0b",
        "secondary": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "baseline": "#c3c2b7",
        "series": ["#2a78d6", "#eb6834", "#1baf7a"],
    },
    "dark": {
        "surface": "#1a1a19",
        "primary": "#ffffff",
        "secondary": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "baseline": "#383835",
        "series": ["#3987e5", "#d95926", "#199e70"],
    },
}

WIDTH, HEIGHT = 880, 380
LEFT, RIGHT, TOP, BOTTOM = 44, 16, 96, 36
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
GAP = 2
RADIUS = 4
Y_MAX = 50


def counts(tidy: pd.DataFrame) -> pd.DataFrame:
    """Return tables reporting each year, one column per chapter."""
    chapter_of = {stem.split("_")[-1]: stem.split("_")[0] for stem in build().files()}
    years = tidy[["table_id", "year"]].drop_duplicates()
    years = years.assign(chapter=years["table_id"].map(chapter_of))
    table = years.groupby(["year", "chapter"]).size().unstack(fill_value=0)
    table = table.reindex(range(FIRST, LAST + 1), fill_value=0)
    return table.reindex(columns=[prefix for prefix, _ in CHAPTERS], fill_value=0)


def _segment(x: float, y: float, width: float, height: float, rounded: bool, fill: str) -> str:
    """One stacked segment; the top one of a column gets the rounded data end."""
    if height <= 0:
        return ""
    if not rounded:
        return (
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" '
            f'height="{height:.2f}" fill="{fill}"/>'
        )
    r = min(RADIUS, width / 2, height)
    bottom = y + height
    return (
        f'<path d="M{x:.2f},{bottom:.2f} V{y + r:.2f} Q{x:.2f},{y:.2f} {x + r:.2f},{y:.2f} '
        f"H{x + width - r:.2f} Q{x + width:.2f},{y:.2f} {x + width:.2f},{y + r:.2f} "
        f'V{bottom:.2f} Z" fill="{fill}"/>'
    )


def svg(table: pd.DataFrame, theme: dict) -> str:
    """Render the stacked columns as an SVG document."""
    plot_w, plot_h = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM
    band = plot_w / len(table)
    bar = min(24.0, band - GAP)
    unit = plot_h / Y_MAX
    base = TOP + plot_h

    def y_of(value: float) -> float:
        return base - value * unit

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{FONT}" role="img" '
        f'aria-labelledby="title desc">',
        '<title id="title">Tables with data, by year</title>',
        '<desc id="desc">Stacked columns, 1895 to 1945, of how many of the 48 tables report '
        "each year, split into education, hygiene and welfare. None report 1895 or 1896. "
        "Coverage rises from 6 tables in 1897 to a plateau of about 47 in the 1930s and "
        "falls from 43 in 1942 to 15 in 1943. The counts are in coverage.csv.</desc>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{theme["surface"]}"/>',
        f'<text x="{LEFT}" y="28" font-size="16" font-weight="600" fill="{theme["primary"]}">'
        "Tables with data, by year</text>",
        f'<text x="{LEFT}" y="48" font-size="12" fill="{theme["secondary"]}">'
        "48 tables from the 1946 compendium, education, hygiene and welfare chapters</text>",
    ]

    # Legend in one row above the plot.
    x = LEFT
    for (_, name), colour in zip(CHAPTERS, theme["series"], strict=True):
        parts.append(f'<rect x="{x}" y="64" width="10" height="10" rx="2" fill="{colour}"/>')
        parts.append(
            f'<text x="{x + 16}" y="73" font-size="12" fill="{theme["secondary"]}">{name}</text>'
        )
        x += 16 + 8 * len(name) + 20

    # Recessive grid and axis.
    for value in range(10, Y_MAX + 1, 10):
        y = y_of(value)
        parts.append(
            f'<line x1="{LEFT}" y1="{y:.2f}" x2="{WIDTH - RIGHT}" y2="{y:.2f}" '
            f'stroke="{theme["grid"]}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{LEFT - 8}" y="{y + 4:.2f}" font-size="11" text-anchor="end" '
            f'fill="{theme["muted"]}">{value}</text>'
        )
    parts.append(
        f'<line x1="{LEFT}" y1="{base:.2f}" x2="{WIDTH - RIGHT}" y2="{base:.2f}" '
        f'stroke="{theme["baseline"]}" stroke-width="1"/>'
    )

    # Columns, bottom chapter first, a surface gap between segments.
    for index, (year, row) in enumerate(table.iterrows()):
        x = LEFT + index * band + (band - bar) / 2
        filled = [(value, colour) for value, colour in zip(row, theme["series"], strict=True)]
        top_index = max((i for i, (value, _) in enumerate(filled) if value), default=-1)
        level = 0.0
        for i, (value, colour) in enumerate(filled):
            if not value:
                continue
            top, bottom = y_of(level + value), y_of(level)
            height = bottom - top - (GAP if level else 0)
            parts.append(_segment(x, top, bar, height, i == top_index, colour))
            level += value
        if year % 5 == 0:
            parts.append(
                f'<text x="{x + bar / 2:.2f}" y="{base + 18:.2f}" font-size="11" '
                f'text-anchor="middle" fill="{theme["muted"]}">{year}</text>'
            )

    # Two things the eye should not have to find unaided, each placed in empty
    # space rather than over a column: the empty first years in two short lines
    # above the lowest columns, and the 1943 fall in the clear band at top right.
    def text(x: float, value: float, body: str, anchor: str) -> None:
        parts.append(
            f'<text x="{x:.2f}" y="{y_of(value):.2f}" font-size="11" '
            f'text-anchor="{anchor}" fill="{theme["secondary"]}">{body}</text>'
        )

    text(LEFT + 2, 12, "1895–96:", "start")
    text(LEFT + 2, 9.4, "none", "start")
    total_1942 = int(table.loc[1942].sum())
    total_1943 = int(table.loc[1943].sum())
    text(WIDTH - RIGHT, 46, f"1943: {total_1942} → {total_1943}", "end")

    parts.append("</svg>")
    return "\n".join(part for part in parts if part) + "\n"


def main() -> int:
    """Write both SVGs and the table view."""
    tidy = pd.read_csv(ROOT / "data" / "tidy.csv")
    table = counts(tidy)
    OUT.mkdir(parents=True, exist_ok=True)
    for mode, name in (("light", "coverage.svg"), ("dark", "coverage-dark.svg")):
        (OUT / name).write_text(svg(table, THEMES[mode]), encoding="utf-8", newline="\n")
    view = table.rename(columns=dict(CHAPTERS)).assign(Total=table.sum(axis=1))
    view.index.name = "year"
    view.to_csv(OUT / "coverage.csv", lineterminator="\n")
    print(f"{OUT}: coverage.svg, coverage-dark.svg, coverage.csv ({len(view)} years)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
