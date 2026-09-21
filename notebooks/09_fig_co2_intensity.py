"""Fig. — CO2e intensity of energy consumption, 2000 vs 2022 (dumbbell).

Source: OLADE/SIELAC, indicator "Indice de emisiones por energia consumida"
[t / tep], one sheet per pollutant (data/raw/Energy_intensity.xlsx).
CO2e = CO2 + GWP(CH4) * CH4, converted from t/tep to g/MJ.
Replaces the R version (Matriz energetica.R, lines 805-834), which used an
older OLADE download (Venezuela 2022 final consumption was overstated).

Design: single dark-grey palette, no grid; the two years are told apart by
hollow marker geometry (2000 = circle, 2022 = triangle) and the change
is read from the length of the bar. Countries run from lowest (bottom) to highest
(top) 2022 intensity.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path

RAW = Path("data/raw")
OUTF = Path("outputs/figures"); OUTF.mkdir(parents=True, exist_ok=True)
OUTT = Path("outputs/tables"); OUTT.mkdir(parents=True, exist_ok=True)

Y0, Y1 = 2000, 2024   # 2024 = latest year of the OLADE release, used as comparison year
G_PER_T = 1e6
MJ_PER_TEP = 41868.0          # OLADE: 1 tep = 10^7 kcal = 41.868 GJ
GWP_CH4 = 28.0                # IPCC AR5, 100-yr (AR4: 25; AR6 fossil: 29.8)
# NO2 in the workbook is nitrogen dioxide, NOT N2O: it has no GWP and is
# excluded. N2O itself was not downloaded, so CO2e here = CO2 + CH4 only.

CORRECTIONS = Path("data/processed/co2_intensity_corrections.csv")
NAMES = {"Brasil": "Brazil", "Perú": "Peru"}
CO2E = "CO₂e"   # carbon dioxide equivalent: subscript 2 (reviewer request)

GREY = "#3b3b3b"    # dark grey for bars and markers
BG = "#FFFCFC"

# font sizes (pt)
FS_YTICK, FS_XTICK, FS_LABEL, FS_LEGEND = 12, 11, 12, 11

# hollow markers: 2000 = circle, 2022 = triangle (larger, so the circle
# still shows inside it when both years are almost equal)
M0, M1 = "o", "^"
S0, S1 = 42, 72           # scatter areas (pt^2)
LW_MARK = 1.0            # marker outline (frame is 0.6)
LW_BAR = 1.7             # magnitude bar
GAP_PT = 1.5               # gap between bar end and marker outline


def load_indicator(sheet_prefix):
    """One pollutant sheet -> DataFrame (country x year), t/tep."""
    xls = pd.ExcelFile(RAW / "Energy_intensity.xlsx")
    sheet = next(s for s in xls.sheet_names if s.startswith(sheet_prefix))
    raw = pd.read_excel(xls, sheet_name=sheet, header=None)
    years = [int(y) for y in raw.iloc[4, 1:]]
    body = raw.iloc[5:, :].dropna(subset=[0])
    body = body[~body[0].astype(str).str.startswith("Fuente")]
    df = body.set_index(0)
    df.columns = years
    df.index = [NAMES.get(c.strip(), c.strip()) for c in df.index]
    return df.apply(pd.to_numeric, errors="coerce")


def build_table():
    co2 = load_indicator("1.")
    ch4 = load_indicator("4.")
    co2e_t_tep = co2 + GWP_CH4 * ch4
    g_mj = co2e_t_tep * G_PER_T / MJ_PER_TEP
    out = pd.DataFrame({
        f"co2_g_mj_{Y0}": co2[Y0] * G_PER_T / MJ_PER_TEP,
        f"co2_g_mj_{Y1}": co2[Y1] * G_PER_T / MJ_PER_TEP,
        f"co2e_g_mj_{Y0}": g_mj[Y0],
        f"co2e_g_mj_{Y1}": g_mj[Y1],
    })
    out[f"olade_indicator_co2e_g_mj_{Y0}"] = out[f"co2e_g_mj_{Y0}"]
    out["corrected"] = False
    if CORRECTIONS.exists():
        # Documented corrections of OLADE values that fail cross-checks
        # (see data/sources.md). The corrected CO2 value is scaled by the
        # indicator's own CO2e/CO2 ratio (CH4 uplift, ~0.1%).
        for _, r in pd.read_csv(CORRECTIONS).iterrows():
            if int(r["year"]) != Y0:
                continue
            c = r["country"]
            uplift = out.loc[c, f"co2e_g_mj_{Y0}"] / out.loc[c, f"co2_g_mj_{Y0}"]
            out.loc[c, f"co2_g_mj_{Y0}"] = r["corrected_co2_g_mj"]
            out.loc[c, f"co2e_g_mj_{Y0}"] = r["corrected_co2_g_mj"] * uplift
            out.loc[c, "corrected"] = True
    # Change Y0 -> Y1 expressed relative to the comparison year (Y1), as in
    # the original R figure; sign kept (+ = intensity rose). Not drawn: the
    # bar length carries the magnitude.
    out["pct_change"] = ((out[f"co2e_g_mj_{Y1}"] - out[f"co2e_g_mj_{Y0}"])
                         / out[f"co2e_g_mj_{Y1}"] * 100)
    out[f"ch4_share_pct_{Y1}"] = (GWP_CH4 * ch4[Y1] / co2e_t_tep[Y1]) * 100
    out.index.name = "country"
    return out.sort_values(f"co2e_g_mj_{Y1}", ascending=True)   # lowest first


def make_figure(tbl, outfile):
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": "#222222"})
    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=BG)
    ax.set_facecolor(BG)
    fig.subplots_adjust(left=0.12, right=0.86, top=0.96, bottom=0.17)

    n = len(tbl)
    ypos = np.arange(n)            # first row (lowest Y1 value) at the bottom
    a, b = tbl[f"co2e_g_mj_{Y0}"].values, tbl[f"co2e_g_mj_{Y1}"].values
    ax.set_xlim(0, max(a.max(), b.max()) * 1.08)
    ax.set_ylim(-0.7, n - 0.3)

    # bars stop at the marker outlines (markers are hollow, so the bar must
    # not run through them)
    ax_width_pt = ax.get_position().width * fig.get_figwidth() * 72
    pt_per_unit = ax_width_pt / np.diff(ax.get_xlim())[0]
    r0 = np.sqrt(S0) / 2 + LW_MARK / 2 + GAP_PT
    # triangle: half-width at mid-height (where the bar meets it) is a quarter of its size
    r1 = np.sqrt(S1) / 4 + LW_MARK / 2 + GAP_PT
    for y, x0, x1 in zip(ypos, a, b):
        sign = np.sign(x1 - x0)
        if abs(x1 - x0) * pt_per_unit <= r0 + r1:
            continue                                   # markers touch: no bar
        ax.plot([x0 + sign * r0 / pt_per_unit, x1 - sign * r1 / pt_per_unit],
                [y, y], color=GREY, lw=LW_BAR, solid_capstyle="butt", zorder=2)
    ax.scatter(a, ypos, s=S0, marker=M0, facecolors="none", edgecolors=GREY,
               linewidths=LW_MARK, zorder=3)          # Y0
    ax.scatter(b, ypos, s=S1, marker=M1, facecolors="none", edgecolors=GREY,
               linewidths=LW_MARK, zorder=4)          # Y1

    ax.set_yticks(ypos)
    ax.set_yticklabels(tbl.index, fontsize=FS_YTICK, color="#333333")
    ax.set_xlabel(f"Emissions intensity of energy consumption\n(g {CO2E} per MJ)",
                  fontsize=FS_LABEL, color="#333333")
    ax.grid(False)
    for sp in ax.spines.values():          # thin frame around the plotting area
        sp.set_visible(True)
        sp.set_linewidth(0.6)
        sp.set_color(GREY)
    ax.tick_params(length=0)
    ax.tick_params(axis="x", labelsize=FS_XTICK)

    handles = [Line2D([], [], marker=M0, ls="", markerfacecolor="none",
                      markeredgecolor=GREY, markeredgewidth=LW_MARK,
                      markersize=np.sqrt(S0), label=str(Y0)),
               Line2D([], [], marker=M1, ls="", markerfacecolor="none",
                      markeredgecolor=GREY, markeredgewidth=LW_MARK,
                      markersize=np.sqrt(S1), label=str(Y1))]
    ax.legend(handles=handles, title="Year", frameon=False, loc="center left",
              bbox_to_anchor=(1.02, 0.5), fontsize=FS_LEGEND,
              title_fontsize=FS_LEGEND, labelspacing=1.0, handletextpad=0.8)

    fig.savefig(outfile, dpi=200, facecolor=BG)
    return fig


if __name__ == "__main__":
    tbl = build_table()
    print(tbl.round(1).to_string())
    col = f"ch4_share_pct_{Y1}"
    print(f"\nCH4 share of CO2e in {Y1}: max {tbl[col].max():.2f}% ({tbl[col].idxmax()})")
    table_path = OUTT / f"co2_intensity_{Y0}_{Y1}.csv"
    tbl.round(3).to_csv(table_path)
    make_figure(tbl, OUTF / "fig_co2_intensity.png")
    print(f"\nSaved -> {OUTF/'fig_co2_intensity.png'}, {table_path}")
