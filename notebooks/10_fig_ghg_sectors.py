"""Fig. — GHG emissions by sector, South America, 2023 (waterfall).

Source: Climate Watch (via manipulaciondata.R), data/raw/GHG_World_sectors_SA.xlsx,
sheet "2023", the 12 South American countries. Replaces the R version
(CO2.R, ~l. 649-832), which built this with ggplot2.

Ten Climate Watch subsectors, excluding "Energy" (the aggregate of
Transportation/Electricity-Heat/Fugitive/Manufacturing-Construction/
Building/Other Fuel Combustion/Bunker Fuels — counting it too would
double-count its own children) and "Waste" (not in the reference figure).

NOTE ON NUMBERS: the reference PNG (an older pull of this same file) had
Agriculture > LUCF and a total of 2,847 MtCO2e. Climate Watch revises LUCF
and Agriculture accounting fairly often; the current download gives LUCF >
Agriculture and a total of 3,649 MtCO2e. Sectors and method are unchanged —
only the vintage of the source data is newer.

Design: DejaVu Sans / grey #3b3b3b / 14pt axis text, matching notebooks
08 and 09. No SUM bar, no per-bar total labels, no legend (sectors are
already named on the x-axis) — replaced by two INDEPENDENT y-axes (each
its own scale, not a rescale of the other): left in MtCO2e, fixed at a
1,400 MtCO2e ceiling, for the grey "own total" bars; right in % of the
10-sector total (0-100%), for the colored floating waterfall bars. Both
axes are drawn in plain black so the pairing (grey bars <-> left axis,
colored bars <-> right axis) is read from which bars fit which scale, not
from axis color. Explicitly requested for this chart; contrast with Fig. 1,
where a twin axis was tried and dropped as confusing.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from pathlib import Path

RAW = Path("data/raw")
OUTF = Path("outputs/figures"); OUTF.mkdir(parents=True, exist_ok=True)
OUTT = Path("outputs/tables"); OUTT.mkdir(parents=True, exist_ok=True)

YEAR = 2023
EXCLUDE = {"Energy", "Waste"}  # see module docstring

# same dark-navy -> pale-yellow ramp as the CO2.R reference figure, minus
# its 11th step (that one coloured the now-removed SUM bar)
COLORS = ["#061B24", "#003f5c", "#2f4b7c", "#665191", "#a05195",
          "#d45087", "#f95d6a", "#ff4500", "#ff7c43", "#ffa600"]

# Typography matched to notebooks/08 and 09
GREY = "#3b3b3b"       # x-axis (sector names) and plot frame
AXIS_COLOR = "#000000"  # both y-axes (ticks, labels, spine) — plain black
MTCO2_MAX = 1400        # fixed ceiling of the left (MtCO2e) axis
# font sizes matched to notebooks/09's dumbbell chart (not 08's 14pt), +5pt
FS_TICK, FS_LABEL = 16, 17
DPI = 600


def load_table():
    d = pd.read_excel(RAW / "GHG_World_sectors_SA.xlsx", sheet_name=str(YEAR))
    sub = d[~d["Subsector"].isin(EXCLUDE)]
    tot = sub.groupby("Subsector")["value"].sum().sort_values(ascending=False)
    out = tot.to_frame("MtCO2e")
    out["pct"] = out["MtCO2e"] / out["MtCO2e"].sum() * 100
    out["cum_end"] = out["MtCO2e"].cumsum()
    out["cum_start"] = out["cum_end"] - out["MtCO2e"]
    out.index.name = "sector"
    return out


def make_figure(tbl, outfile):
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": "#222222"})
    n = len(tbl)
    fig, ax = plt.subplots(figsize=(19, 8.6), facecolor="white")

    x = np.arange(n)
    colors = COLORS[:n]
    grand_total = tbl["MtCO2e"].sum()
    cum_pct_end = tbl["cum_end"] / grand_total * 100
    cum_pct_start = tbl["cum_start"] / grand_total * 100

    # grey "own total" bars: each sector's value measured from zero, as a
    # size reference — plotted on the left (MtCO2e) axis
    ax.bar(x, tbl["MtCO2e"], bottom=0, color="#d9d9d9", width=0.68, zorder=1)

    # right axis, created before any right-axis styling (twinx() resets
    # tick side on ax if done after)
    ax2 = ax.twinx()

    # the actual waterfall bars, floating at their cumulative offset —
    # plotted on the right (%) axis, independent of the left axis's scale
    ax2.bar(x, tbl["pct"], bottom=cum_pct_start, color=colors,
            width=0.68, zorder=3)

    # dotted connector between the top of bar i and the start of bar i+1
    # (the classic waterfall "staircase" cue, doing the job the removed
    # per-bar total labels used to do) — on the % axis, alongside the
    # colored bars it connects
    for i in range(n - 1):
        ax2.plot([x[i] + 0.34, x[i + 1] - 0.34],
                 [cum_pct_end.iloc[i]] * 2,
                 ls=":", color=GREY, lw=1.1, zorder=2)

    ax.set_ylim(0, MTCO2_MAX)
    ax2.set_ylim(0, 103)
    ax.set_xlim(-0.6, n - 0.4)

    # horizontal, wrapped onto 1-2 short lines instead of diagonal, so
    # adjacent labels don't collide
    WRAP = {
        "Land Use, Land-Use Change and Forestry": "LUCF",
        "Manufacturing/Construction": "Manufacturing\nConstruction",
        "Electricity/Heat": "Electricity\nHeat",
        "Fugitive Emissions": "Fugitive\nEmissions",
        "Other Fuel Combustion": "Other Fuel\nCombustion",
        "Industrial Processes": "Industrial\nProcesses",
        "Bunker Fuels": "Bunker\nFuels",
    }
    labels = [WRAP.get(s, s) for s in tbl.index]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FS_TICK, color=GREY, ha="center")

    # left axis: MtCO2e, fixed 0-1500 ceiling — grey bars measured against it
    ax.yaxis.tick_left()               # twinx() above reset this; reassert
    ax.set_ylabel("Emissions (MtCO$_2$e)", fontsize=FS_LABEL, color=AXIS_COLOR, labelpad=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.tick_params(axis="y", labelsize=FS_TICK, colors=AXIS_COLOR, length=3)
    ax.tick_params(axis="x", length=0)

    # right axis: independent 0-100% scale — colored waterfall bars measured
    # against it
    ax2.yaxis.tick_right()
    pct_ticks = list(range(0, 101, 10))
    ax2.set_yticks(pct_ticks)
    ax2.set_yticklabels([f"{p}%" for p in pct_ticks], fontsize=FS_TICK, color=AXIS_COLOR)
    ax2.set_ylabel("Share of total (%)", fontsize=FS_LABEL, color=AXIS_COLOR, labelpad=10)
    ax2.tick_params(axis="y", length=3, colors=AXIS_COLOR)

    ax.grid(False)
    for spine in ax.spines.values():              # thin frame, matches 08/09
        spine.set_visible(True)
        spine.set_color(GREY)
        spine.set_linewidth(0.8)
    for side in ("top", "bottom", "left"):
        ax2.spines[side].set_visible(False)       # ax already draws these
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(AXIS_COLOR)
    ax2.spines["right"].set_linewidth(0.8)

    fig.subplots_adjust(left=0.08, right=0.90, top=0.96, bottom=0.13)
    fig.savefig(outfile, dpi=DPI, facecolor="white")
    # vector copy: resolution-independent, but dpi still governs any
    # raster-based sizing/metrics matplotlib applies internally
    fig.savefig(outfile.with_suffix(".svg"), dpi=DPI, facecolor="white")
    return fig


if __name__ == "__main__":
    tbl = load_table()
    print(tbl.round(1).to_string())
    print(f"\nTotal: {tbl['MtCO2e'].sum():,.1f} MtCO2e ({YEAR}, 12 SA countries, "
          f"excludes {', '.join(sorted(EXCLUDE))})")
    table_path = OUTT / f"ghg_sectors_{YEAR}.csv"
    tbl.round(2).to_csv(table_path)
    make_figure(tbl, OUTF / "fig_ghg_sectors.png")
    print(f"Saved -> {OUTF/'fig_ghg_sectors.png'}, {OUTF/'fig_ghg_sectors.svg'}, {table_path}")
