"""Fig. — South America's share of world mine production and reserves,
key energy-transition minerals, 2023 (stacked bar + reserve-share dot).

Source: USGS Mineral Commodity Summaries 2024 (see data/sources.md for the
per-country production/reserves figures and the exact URLs). Replaces the R
version (manipulaciondata.R, l. 155-178): its `Minerals.xlsx` input only
ever existed in a Downloads folder on the previous machine and wasn't
recoverable, so this rebuilds the table straight from the public USGS PDFs
instead (see data/sources.md for the cross-check against the old reference
figure — bar and dot values reproduce it almost exactly).

Method: each country's bar segment = its 2023 estimated mine production /
world 2023 mine production; the black dot = the summed reserves of the SA
countries with any production, as a share of world reserves. A country with
no reported production for a mineral contributes 0 (most minerals: only
1-4 of the 5 countries produce it at all).

Design: same parameters as notebooks 08-10 (DejaVu Sans, grey #3b3b3b, thin
frame, matched axis text size, 600 dpi + SVG). Palette: countries, not
fuels, so a *different* palette from notebook 08's fuel ramp is used
deliberately (the dataviz skill's validated 8-hue categorical set, first 5
slots, fixed order) rather than reusing/extending the fuel-type gradient.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

PROCESSED = Path("data/processed")  # hand-transcribed source table, see data/sources.md
OUTF = Path("outputs/figures"); OUTF.mkdir(parents=True, exist_ok=True)
OUTT = Path("outputs/tables"); OUTT.mkdir(parents=True, exist_ok=True)

MINERALS = ["Copper", "Graphite", "Lithium", "Nickel", "Rare earths", "Silver"]
# stacking order bottom -> top (reverse-alphabetical, matches the R original)
COUNTRIES = ["Peru", "Chile", "Brazil", "Bolivia", "Argentina"]

# categorical palette: countries are an identity, not a magnitude, so this is
# a fixed-order hue set — deliberately NOT the fuel-type gradient from
# notebooks 08/10, so this chart doesn't read as "another energy-mix figure".
COUNTRY_COLORS = {
    "Argentina": "#051F40",  # dark navy
    "Bolivia":   "#215911",  # dark green
    "Brazil":    "#A67E08",  # dark gold
    "Chile":     "#005C53",  # teal (was the lighter #558C03 green)
    "Peru":      "#8C4F04",  # dark brown
}

GREY = "#3b3b3b"
FS_TICK, FS_LABEL = 16, 17
DPI = 600


def load_table():
    df = pd.read_csv(PROCESSED / "minerals_usgs_mcs2024.csv")
    df["mineral"] = pd.Categorical(df["mineral"], categories=MINERALS, ordered=True)
    world = df[df["country"] == "World"].set_index("mineral")
    countries = df[df["country"] != "World"].copy()
    countries["prod_share_pct"] = countries.apply(
        lambda r: r["production_2023e"] / world.loc[r["mineral"], "production_2023e"] * 100,
        axis=1)
    countries["reserve_share_pct"] = countries.apply(
        lambda r: (r["reserves"] / world.loc[r["mineral"], "reserves"] * 100)
        if world.loc[r["mineral"], "reserves"] else 0.0, axis=1)
    return countries, world


def make_figure(countries, world, outfile):
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": "#222222"})
    fig, ax = plt.subplots(figsize=(11, 6.5), facecolor="white")

    x = np.arange(len(MINERALS))
    bottoms = np.zeros(len(MINERALS))
    for country in COUNTRIES:
        vals = np.array([
            countries.loc[(countries["mineral"] == m) & (countries["country"] == country),
                          "prod_share_pct"].sum()
            for m in MINERALS
        ])
        ax.bar(x, vals, bottom=bottoms, width=0.62, color=COUNTRY_COLORS[country],
               label=country, zorder=2)
        bottoms += vals

    # reserve-share dot: summed SA reserves (of countries that produce it) / world reserves
    reserves_sa = countries.groupby("mineral", observed=True)["reserves"].sum().reindex(MINERALS)
    reserve_dot = (reserves_sa / world["reserves"].reindex(MINERALS) * 100).values
    ax.scatter(x, reserve_dot, color="black", s=70, zorder=3)

    ymax = max(bottoms.max(), np.nanmax(reserve_dot)) * 1.12
    ax.set_ylim(0, ymax)
    ax.set_xlim(-0.6, len(MINERALS) - 0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(MINERALS, fontsize=FS_TICK, color=GREY)
    ax.tick_params(axis="x", length=0)
    ax.tick_params(axis="y", length=3, labelsize=FS_TICK, colors=GREY)

    ax.grid(False)
    # corner "%" unit tag (not a rotated axis title) — matches the reference figure
    ax.annotate("%", xy=(-0.055, 1.02), xycoords="axes fraction",
                ha="left", va="bottom", fontsize=FS_LABEL, color=GREY)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(GREY)
        spine.set_linewidth(0.8)

    handles, labels = ax.get_legend_handles_labels()
    order = [labels.index(c) for c in sorted(COUNTRY_COLORS)]  # alphabetical in the legend
    ax.legend([handles[i] for i in order], [labels[i] for i in order],
              frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=FS_TICK - 2, labelspacing=0.8)

    fig.subplots_adjust(left=0.09, right=0.84, top=0.90, bottom=0.10)
    fig.savefig(outfile, dpi=DPI, bbox_inches="tight", facecolor="white")
    fig.savefig(outfile.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    return fig


if __name__ == "__main__":
    countries, world = load_table()
    pivot = countries.pivot(index="mineral", columns="country", values="prod_share_pct") \
                      .reindex(MINERALS)[COUNTRIES[::-1]]
    print(pivot.round(1).to_string())
    reserves_sa = countries.groupby("mineral", observed=True)["reserves"].sum().reindex(MINERALS)
    reserve_dot = reserves_sa / world["reserves"].reindex(MINERALS) * 100
    print("\nReserve share (dot), %:")
    print(reserve_dot.round(1).to_string())

    table_path = OUTT / "minerals_sa_share_2023.csv"
    countries.round(3).to_csv(table_path, index=False)
    make_figure(countries, world, OUTF / "fig_minerals.png")
    print(f"\nSaved -> {OUTF/'fig_minerals.png'}, {OUTF/'fig_minerals.svg'}, {table_path}")
