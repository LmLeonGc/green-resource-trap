import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pathlib import Path

RAW = Path("data/raw")
OUTF = Path("outputs/figures"); OUTF.mkdir(parents=True, exist_ok=True)

FOSSIL_PRIMARY = ["PETRÓLEO", "GAS NATURAL", "CARBÓN MINERAL"]
FOSSIL_DERIVED = [
    "GAS LICUADO DE PETRÓLEO","GASOLINA SIN ETANOL","GASOLINA CON ETANOL",
    "KEROSENE/JET FUEL","DIÉSEL OIL SIN BIODIÉSEL","DIÉSEL OIL CON BIODIÉSEL",
    "FUEL OIL","COQUE","GASES",
]
PRIMARY_ALL = [
    "PETRÓLEO","GAS NATURAL","CARBÓN MINERAL","NUCLEAR","HIDROENERGÍA",
    "GEOTERMIA","EÓLICA","SOLAR","LEÑA","BAGAZO DE CAÑA","ETANOL",
    "BIODIÉSEL","BIOGÁS","OTRA BIOMASA","OTRAS PRIMARIAS",
]
# For the stacked composition we group sources into readable categories.
# Order = bottom -> top of the stack (mirrors the reference figure: dense
# fossil base at the bottom, light renewables at the top).
GROUPS = {
    "Oil":              ["PETRÓLEO"],
    "Natural Gas":      ["GAS NATURAL"],
    "Other":            ["OTRAS PRIMARIAS"],
    "Mineral Coal":     ["CARBÓN MINERAL"],
    "Hydropower":       ["HIDROENERGÍA"],
    "Nuclear":          ["NUCLEAR"],
    "Biomass":          ["LEÑA","BAGAZO DE CAÑA","ETANOL","BIODIÉSEL","BIOGÁS","OTRA BIOMASA"],
    "Other renewables": ["GEOTERMIA","EÓLICA","SOLAR"],
}

# ---- Visual style replicating the reference image (flat, opaque) ----------
# Palette matched to the reference: very dark teal-navy fossil base ->
# indigo -> blue-violet -> purple -> magenta -> coral -> light pink -> yellow.
GROUP_COLORS = {
    "Oil":              "#1a3a4a",  # very dark teal-navy (dense fossil base)
    "Natural Gas":      "#2e3a6e",  # deep indigo
    "Other":            "#4b4b8f",  # blue-violet
    "Mineral Coal":     "#8a4a9e",  # purple
    "Hydropower":       "#c0398f",  # magenta
    "Biomass":          "#e8556b",  # coral / salmon-red (Firewood-like band)
    "Nuclear":          "#f4a0c0",  # light pink
    "Other renewables": "#f4d03f",  # solar/wind yellow
}
# Years that get a total "lollipop" on top and inline % labels.
LABEL_YEARS = [1990, 2000, 2010, 2022]
# X-axis tick labels (kept separate so the axis starts clean at 1990).
XTICK_YEARS = [1990, 2000, 2010, 2022]
UNIT = "10³ bep"          # keep the working unit (bep), not MJ
INLINE_PCT_MIN = 5.0      # only annotate inline % for bands at/above this share
BAND_ALPHA = 1.0          # flat, opaque bands (no transparency) — matches ref


def _norm(s): return str(s).strip().upper()

def _row(raw, cols, label):
    fc = raw.iloc[:,0].apply(_norm)
    m = fc.eq(_norm(label))
    if not m.any(): return None
    r = raw[m].iloc[0]; r.index = cols
    return pd.to_numeric(r, errors="coerce")

def load_series(filename):
    xls = pd.ExcelFile(RAW / filename)
    records = {}
    for sheet in xls.sheet_names:
        s = sheet.strip()
        # sheets look like "1990 - América del Sur"
        if "del sur" not in s.lower():
            continue
        try:
            year = int(s.split("-")[0].strip())
        except ValueError:
            continue
        raw = pd.read_excel(xls, sheet_name=sheet, header=None)
        hdr = raw.apply(lambda r: r.astype(str).str.contains("PETRÓLEO", na=False).any(), axis=1).idxmax()
        cols = [_norm(c) for c in raw.iloc[hdr].tolist()]
        oferta = _row(raw, cols, "OFERTA TOTAL")
        imp    = _row(raw, cols, "IMPORTACIÓN")
        exp    = _row(raw, cols, "EXPORTACIÓN")
        if oferta is None: continue

        def grab(series, names):
            if series is None: return 0.0
            present = [_norm(n) for n in names if _norm(n) in series.index]
            return series[present].fillna(0).sum()

        deriv_net = max(grab(imp, FOSSIL_DERIVED) - grab(exp, FOSSIL_DERIVED), 0.0)
        # composition by group (primary supply)
        comp = {g: grab(oferta, names) for g, names in GROUPS.items()}
        # add net-imported fossil derivatives into the fossil side (Oil proxy)
        comp["Oil"] += deriv_net
        total = sum(comp.values())
        fossil = comp["Oil"] + comp["Natural Gas"] + comp["Mineral Coal"]
        records[year] = {**comp, "TOTAL": total, "fossil_share": fossil/total*100}
    df = pd.DataFrame(records).T.sort_index()
    return df


def _fmt_value(v):
    """Scientific-notation label like the reference image: 2.81E06."""
    if v <= 0 or np.isnan(v):
        return "0"
    exp = int(np.floor(np.log10(v)))
    mant = v / (10 ** exp)
    return f"{mant:.2f}E{exp:02d}"


def _darken(hex_color, factor=0.62):
    """Return a darker version of a hex colour for legible text labels."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = (int(c * factor) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten(hex_color, factor=0.72):
    """Return a lighter tint of a hex colour (blend toward white) for
    legible, on-tone inline labels that are not pure white."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = (int(c + (255 - c) * factor) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def make_figure(df, group_cols, outfile):
    # ---- typography & canvas ------------------------------------------------
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.edgecolor": "#888888",
        "text.color": "#222222",
    })
    fig, ax = plt.subplots(figsize=(12.5, 6.0))

    x = df.index.values.astype(float)
    colors = [GROUP_COLORS[g] for g in group_cols]

    # ---- stacked area -------------------------------------------------------
    stacks = ax.stackplot(
        x, *[df[g].values for g in group_cols],
        colors=colors, linewidth=0, edgecolor="none", alpha=BAND_ALPHA,
    )

    # cumulative tops for label placement
    cum = np.zeros_like(x, dtype=float)
    band_bottom = {}
    band_top = {}
    for g in group_cols:
        band_bottom[g] = cum.copy()
        cum = cum + df[g].values
        band_top[g] = cum.copy()
    total = cum  # == df["TOTAL"]

    xmin, xmax = x.min(), x.max()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(0, total.max() * 1.10)   # modest headroom for the top labels

    # ---- external right-side labels (name + value + %) ----------------------
    last = -1  # last year column
    label_x = xmax + (xmax - xmin) * 0.012
    # mid-height of each band at the final year, used as the anchor y
    anchors = []
    for g in group_cols:
        y_mid = (band_bottom[g][last] + band_top[g][last]) / 2.0
        anchors.append([g, y_mid])

    # spread overlapping labels vertically so they don't collide
    anchors.sort(key=lambda t: t[1])
    min_gap = total.max() * 0.072
    for i in range(1, len(anchors)):
        if anchors[i][1] - anchors[i-1][1] < min_gap:
            anchors[i][1] = anchors[i-1][1] + min_gap

    for g, y in anchors:
        val = df[g].values[last]
        pct = val / total[last] * 100
        ax.annotate(
            f"{g}\n{_fmt_value(val)} {UNIT} ({pct:.2f}%)",
            xy=(xmax, (band_bottom[g][last] + band_top[g][last]) / 2.0),
            xytext=(label_x, y),
            va="center", ha="left", fontsize=11, color=GROUP_COLORS[g],
            fontweight="bold",
            annotation_clip=False,
        )

    # ---- total "lollipops" on top at selected years -------------------------
    # Line rises from the band top (the total, marked with a dot) up to the label.
    for yr in LABEL_YEARS:
        if yr not in df.index:
            continue
        xi = float(yr)
        top = total[df.index.get_loc(yr)]
        y_label = ax.get_ylim()[1] * 0.99
        ax.plot([xi, xi], [top, y_label * 0.965], color="#222222", lw=1.2, zorder=5)
        ax.scatter([xi], [top], color="#222222", s=22, zorder=6)
        ax.text(xi, y_label, f"{_fmt_value(total[df.index.get_loc(yr)])} {UNIT}",
                ha="center", va="bottom", fontsize=12, fontweight="bold",
                color="#111111")

    # ---- inline % labels on the big bands at selected years -----------------
    # Each label is a light tint of its own band colour (not pure white), which
    # keeps contrast on dark bands while staying on-tone.
    skip_years = {df.index.min(), df.index.max()}  # crowded edges -> no labels
    for yr in LABEL_YEARS:
        if yr not in df.index:
            continue
        # first year: thin bands crowd the left edge and white text disappears;
        # last year: shares already shown in the external right-hand labels
        if yr in skip_years:
            continue
        idx = df.index.get_loc(yr)
        xi = float(yr)
        for g in group_cols:
            share = df[g].values[idx] / total[idx] * 100
            if share < INLINE_PCT_MIN:
                continue
            y_mid = (band_bottom[g][idx] + band_top[g][idx]) / 2.0
            txt_color = _lighten(GROUP_COLORS[g])   # light tint of the band tone
            x_off = (xmax - xmin) * 0.018           # nudge slightly to the right
            ax.text(xi + x_off, y_mid, f"{share:.2f}%", ha="center", va="center",
                    fontsize=12, fontweight="bold", color=txt_color)

    # ---- axis cosmetics -----------------------------------------------------
    ax.set_yticks([])                      # no y-axis ticks (matches the image)
    xticks = [y for y in XTICK_YEARS if xmin <= y <= xmax]
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(y) for y in xticks], fontsize=17, fontweight="bold",
                       color="#222222")
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#888888")
    ax.tick_params(axis="x", length=0)
    ax.margins(x=0)

    # leave room on the right for the external labels
    fig.subplots_adjust(left=0.02, right=0.78, top=0.92, bottom=0.08)
    fig.savefig(outfile, dpi=200, bbox_inches="tight", facecolor="white")
    return fig


if __name__ == "__main__":
    df = load_series("Matriz_balance_energetico_serie.xlsx")  # adjust filename
    print(df[["TOTAL","fossil_share"]].round(1).to_string())
    print(f"\nFossil share {df.index[0]}: {df['fossil_share'].iloc[0]:.1f}%")
    print(f"Fossil share latest ({df.index[-1]}): {df['fossil_share'].iloc[-1]:.1f}%")

    group_cols = list(GROUPS.keys())
    make_figure(df, group_cols, OUTF / "fig1_energy_matrix.png")
    print(f"\nSaved -> {OUTF/'fig1_energy_matrix.png'}")
    