import colorsys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
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
# Every adjacent pair is spaced in both lightness and hue (checked so no two
# neighbours land within ~20 luma points of each other), same hue journey
# and order as the reference, just pushed further apart.
GROUP_COLORS = {
    "Oil":              "#0b2532",  # very dark teal-navy (dense fossil base)
    "Natural Gas":      "#1e3576",  # indigo
    "Other":            "#4b419f",  # blue-violet
    "Mineral Coal":     "#a54fc4",  # orchid-purple
    "Hydropower":       "#c2298f",  # magenta
    "Biomass":          "#e45864",  # coral / salmon-red (Firewood-like band)
    "Nuclear":          "#f49ab8",  # light pink
    "Other renewables": "#f4d03f",  # solar/wind yellow
}
UNIT = "10³ bep"          # keep the working unit (bep), not MJ
BAND_ALPHA = 1.0          # flat, opaque bands (no transparency) — matches ref
XTICK_STEP = 5            # regular x-axis grid, every 5 years

# Typography: all axes (x years, both y-axes, axis titles) at one uniform size
GREY = "#3b3b3b"
FS_YTICK = FS_XTICK = FS_LABEL = 14
N_Y_TICKS = 6              # left (%) and right (bep) magnitude axes


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


def _saturate(hex_color, s_target=1.0):
    """Raise a colour's HSL saturation (same hue/lightness) before it goes
    through _lighten(): blending straight toward white in RGB crushes
    saturation fastest on dark, low-lightness colours (e.g. Oil), so they
    come out grey instead of a pale tint of their own hue."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    hh, l, _ = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(hh, l, s_target)
    return f"#{round(r2*255):02x}{round(g2*255):02x}{round(b2*255):02x}"


def make_figure(df, group_cols, outfile, light_fill=False, fill_factor=0.60):
    """light_fill=True: pale tint fill per band + a boundary line in the
    band's full colour (v2 experiment for telling adjacent bands apart)."""
    # ---- typography & canvas ------------------------------------------------
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.edgecolor": "#888888",
        "text.color": "#222222",
    })
    fig, ax = plt.subplots(figsize=(12.5, 6.0))

    x = df.index.values.astype(float)

    # ---- stacked area, cumulative tops for label placement -----------------
    cum = np.zeros_like(x, dtype=float)
    band_bottom = {}
    band_top = {}
    for g in group_cols:
        band_bottom[g] = cum.copy()
        cum = cum + df[g].values
        band_top[g] = cum.copy()
    total = cum  # == df["TOTAL"]

    if light_fill:
        # Oil is dark and low-lightness enough that blending it toward white
        # crushes its saturation before the others (comes out grey, not
        # pale blue) — pre-saturate just its fill source, not the boundary
        # line or the legend colour, both of which are already fine.
        fill_source = dict(GROUP_COLORS)
        fill_source["Oil"] = _saturate(GROUP_COLORS["Oil"], 1.0)
        for g in group_cols:
            ax.fill_between(x, band_bottom[g], band_top[g],
                             facecolor=_lighten(fill_source[g], fill_factor),
                             edgecolor="none", zorder=1)
            ax.plot(x, band_top[g], color=GROUP_COLORS[g], lw=1.6, zorder=2)
    else:
        ax.stackplot(
            x, *[df[g].values for g in group_cols],
            colors=[GROUP_COLORS[g] for g in group_cols],
            linewidth=0, edgecolor="none", alpha=BAND_ALPHA,
        )

    xmin, xmax = x.min(), x.max()
    ax.set_xlim(xmin, xmax)
    ymax = total.max() * 1.04            # slim headroom (no top labels anymore)
    ax.set_ylim(0, ymax)

    # Fuel-type labels (name, value, %) removed — added by hand afterwards.

    # ---- axis cosmetics -----------------------------------------------------
    # regular grid every XTICK_STEP years, plus the last data year even if it
    # falls off that grid (e.g. …2010, 2020, 2024)
    first_grid = int(np.ceil(xmin / XTICK_STEP) * XTICK_STEP)
    xticks = list(range(first_grid, int(xmax) + 1, XTICK_STEP))
    if xmin not in xticks and xmin == int(xmin):
        xticks.insert(0, int(xmin))
    last_year = int(xmax)
    if last_year not in xticks:
        # drop the nearest regular tick instead of crowding it against the
        # last-year label (e.g. …2010, 2024 rather than …2010, 2020, 2024)
        if xticks and (last_year - xticks[-1]) < XTICK_STEP / 2:
            xticks.pop()
        xticks.append(last_year)
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(y) for y in xticks], fontsize=FS_XTICK, color=GREY)
    ax.tick_params(axis="x", length=0)
    ax.margins(x=0)

    # left axis: absolute magnitude, the only y-axis (the % twin axis was
    # dropped — it read as confusing rather than clarifying). The working
    # unit is already 10³ bep, so dividing by another 10³ (-> 10⁶ bep) keeps
    # the tick numbers short.
    BEP_DIVISOR, BEP_UNIT = 1_000, "10⁶ bep"
    ax.yaxis.set_label_position("left")
    ax.yaxis.tick_left()
    # same "nice" ticks MaxNLocator would pick, minus 0 (redundant — the
    # bottom spine already marks the baseline)
    bep_ticks = [v for v in MaxNLocator(nbins=N_Y_TICKS).tick_values(0, ymax)
                 if 0 < v <= ymax]
    ax.set_yticks(bep_ticks)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / BEP_DIVISOR:,.0f}"))
    ax.tick_params(axis="y", length=3, labelsize=FS_YTICK, colors=GREY)
    # standard rotated y-axis title, vertically centred on the axis (now
    # safe to use — the composition labels it used to collide with are gone)
    ax.set_ylabel(f"Energy supply ({BEP_UNIT})", fontsize=FS_LABEL, color=GREY,
                  labelpad=12)

    # thin frame around the whole plotting area (matches notebooks/09)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(GREY)
        spine.set_linewidth(0.8)

    # leave room on the left for the rotated axis title; no reserved gutter
    # on the right now that the fuel-type labels are added by hand afterwards
    fig.subplots_adjust(left=0.10, right=0.98, top=0.96, bottom=0.09)
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

    # v2 experiment: pale band fill + boundary line in the band's full colour
    make_figure(df, group_cols, OUTF / "fig1_energy_matrix_v2.png", light_fill=True)
    print(f"Saved -> {OUTF/'fig1_energy_matrix_v2.png'}")
    