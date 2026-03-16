from __future__ import annotations

from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGURES = ROOT / "figs"
FIGURES.mkdir(exist_ok=True)

YEAR_COLS = [str(y) for y in range(1960, 2024)]
HDI_YEARS = list(range(1990, 2024))
EXPECTED_FIGS = [
    "01_hdi_trajectory.png",
    "02_life_expectancy.png",
    "03_under5_mortality.png",
    "04_mean_years_schooling.png",
    "05_expected_years_schooling.png",
    "06_tertiary_enrollment.png",
    "07_maternal_mortality.png",
    "08_hdi_gain_rank.png",
]

# Higher-contrast palette
IRAN_COLOR = "#0B5CAB"      # strong blue
MEDIAN_COLOR = "#D55E00"    # strong orange
PEER_COLOR = "#C9D0D6"      # pale gray-blue
REFERENCE_COLOR = "#444444" # dark neutral
GRID_COLOR = "#D8DDE3"

plt.rcParams.update({
    "figure.dpi": 180,
    "savefig.dpi": 240,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "legend.fontsize": 9,
})


def load_inputs():
    hdi = pd.read_csv(DATA / "HDR25_Composite_indices_complete_time_series.csv", encoding="latin-1")
    le = pd.read_csv(DATA / "WB_WDI_SP_DYN_LE00_IN_WIDEF.csv", low_memory=False)
    u5 = pd.read_csv(DATA / "WB_WDI_SH_DYN_MORT_WIDEF.csv", low_memory=False)
    gs = pd.read_csv(DATA / "WB_GS_WIDEF.csv", low_memory=False)
    hnp = pd.read_csv(DATA / "WB_HNP_WIDEF.csv", low_memory=False)
    return hdi, le, u5, gs, hnp


def build_peer_group(hdi: pd.DataFrame) -> pd.DataFrame:
    iran1990 = float(hdi.loc[hdi["iso3"] == "IRN", "hdi_1990"].iloc[0])
    peer_df = hdi[
        (hdi["hdi_1990"].notna())
        & (hdi["hdi_1990"].between(iran1990 - 0.02, iran1990 + 0.02))
        & (~hdi["iso3"].astype(str).str.startswith("ZZK"))
        & (hdi["iso3"] != "IRN")
    ].copy()
    peer_df["hdi_gain_1990_2023"] = peer_df["hdi_2023"] - peer_df["hdi_1990"]
    peer_df = peer_df.sort_values(["hdi_2023", "country"], ascending=[False, True]).reset_index(drop=True)
    return peer_df


def undp_series(hdi: pd.DataFrame, prefix: str, iso: str) -> pd.DataFrame:
    cols = [f"{prefix}_{y}" for y in HDI_YEARS]
    row = hdi.loc[hdi["iso3"] == iso, cols].iloc[0]
    return pd.DataFrame({"year": HDI_YEARS, "value": pd.to_numeric(row.values, errors="coerce")}).dropna()


def undp_peer_long(hdi: pd.DataFrame, prefix: str, peer_isos: list[str]) -> pd.DataFrame:
    cols = ["iso3", "country"] + [f"{prefix}_{y}" for y in HDI_YEARS]
    tmp = hdi[hdi["iso3"].isin(peer_isos)][cols].melt(
        id_vars=["iso3", "country"], var_name="var", value_name="value"
    )
    tmp["year"] = tmp["var"].str[-4:].astype(int)
    tmp["value"] = pd.to_numeric(tmp["value"], errors="coerce")
    return tmp.drop(columns="var").dropna()


def wb_long(df: pd.DataFrame, indicator: str | None = None, sex: str = "_T") -> pd.DataFrame:
    x = df.copy()
    if indicator is not None:
        x = x[x["INDICATOR"] == indicator]
    if "SEX" in x.columns:
        x = x[x["SEX"] == sex]
    long = x.melt(
        id_vars=[c for c in x.columns if c not in YEAR_COLS],
        value_vars=YEAR_COLS,
        var_name="year",
        value_name="value",
    )
    long["year"] = long["year"].astype(int)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long.dropna(subset=["value"])


def wb_country(long: pd.DataFrame, iso: str) -> pd.DataFrame:
    return long[long["REF_AREA"] == iso][["year", "value"]].sort_values("year")


def wb_peer_long(long: pd.DataFrame, peer_isos: list[str]) -> pd.DataFrame:
    return long[long["REF_AREA"].isin(peer_isos)].copy()


def median_band_from_long(long: pd.DataFrame) -> pd.DataFrame:
    return long.groupby("year")["value"].agg(
        median="median",
        p25=lambda s: s.quantile(0.25),
        p75=lambda s: s.quantile(0.75),
    ).reset_index()


def nice_limits(values: pd.Series, pad_frac: float = 0.08, zero_floor: bool = False, step: float | None = None) -> tuple[float, float]:
    vals = pd.to_numeric(values, errors="coerce").dropna()
    if vals.empty:
        return (0.0, 1.0)
    vmin, vmax = float(vals.min()), float(vals.max())
    if math.isclose(vmin, vmax):
        delta = max(abs(vmax) * 0.1, 1.0)
        return (vmin - delta, vmax + delta)
    rng = vmax - vmin
    lo = vmin - pad_frac * rng
    hi = vmax + pad_frac * rng
    if zero_floor:
        lo = min(lo, 0)
    if step is None:
        raw = (hi - lo) / 6
        if raw <= 1:
            step = 1
        elif raw <= 2:
            step = 2
        elif raw <= 5:
            step = 5
        elif raw <= 10:
            step = 10
        else:
            step = 20
    lo = math.floor(lo / step) * step
    hi = math.ceil(hi / step) * step
    return lo, hi


def plot_all_peers(peer_long: pd.DataFrame, iran: pd.DataFrame, title: str, ylabel: str, path: Path,
                   iso_col: str = "iso3", xlim=None, ylim=None, note: str | None = None, show_median: bool = True):
    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    for iso in sorted(peer_long[iso_col].unique()):
        s = peer_long[peer_long[iso_col] == iso].sort_values("year")
        ax.plot(s["year"], s["value"], color=PEER_COLOR, lw=1.1, alpha=0.95, zorder=1)
    if show_median:
        med = median_band_from_long(peer_long)
        ax.plot(med["year"], med["median"], color=MEDIAN_COLOR, lw=2.6, zorder=3, label="Peer median")
    ax.plot(iran["year"], iran["value"], color=IRAN_COLOR, lw=3.0, zorder=4, label="Iran")
    ax.set_title(title, loc="left")
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    if xlim:
        ax.set_xlim(*xlim)
        tick_step = 5 if (xlim[1] - xlim[0]) >= 20 else 2
        ax.set_xticks(np.arange(int(xlim[0]), int(xlim[1]) + 1, tick_step))
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(axis="y", color=GRID_COLOR, alpha=0.7)
    ax.legend(frameon=False, loc="best")
    if note:
        fig.text(0.01, 0.01, note, ha="left", va="bottom", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_rank(peer_df: pd.DataFrame, hdi: pd.DataFrame):
    rank = peer_df[["iso3", "country", "hdi_gain_1990_2023"]].sort_values("hdi_gain_1990_2023").copy()
    colors = [PEER_COLOR for _ in rank["iso3"]]
    iran_gain = float(hdi.loc[hdi["iso3"] == "IRN", "hdi_2023"].iloc[0] - hdi.loc[hdi["iso3"] == "IRN", "hdi_1990"].iloc[0])
    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    ax.barh(rank["country"], rank["hdi_gain_1990_2023"], color=colors)
    ax.axvline(iran_gain, color=IRAN_COLOR, lw=2.8, label=f"Iran gain ({iran_gain:.3f})")
    ax.set_title("HDI gain, 1990–2023, among the 14 peer countries", loc="left")
    ax.set_xlabel("Absolute HDI gain")
    ax.grid(axis="x", color=GRID_COLOR, alpha=0.7)
    ax.legend(frameon=False, loc="best")
    fig.text(0.01, 0.01, "Iran is a reference line here, not a member of its own peer comparison set.", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURES / "08_hdi_gain_rank.png", bbox_inches="tight")
    plt.close(fig)


# ----- run -----
# clear stale PNGs so the directory state is easy to verify
for name in EXPECTED_FIGS:
    p = FIGURES / name
    if p.exists():
        p.unlink()

hdi, le, u5, gs, hnp = load_inputs()
peer_df = build_peer_group(hdi)
peer_isos = peer_df["iso3"].tolist()

le_long = wb_long(le)
u5_long = wb_long(u5)
ter_long = wb_long(gs, "WB_GS_SE_TER_ENRR")
mmr_long = wb_long(hnp, "WB_HNP_SH_STA_MMRT")

plot_all_peers(
    undp_peer_long(hdi, "hdi", peer_isos),
    undp_series(hdi, "hdi", "IRN"),
    "HDI trajectory: Iran against all 14 peer countries",
    "HDI",
    FIGURES / "01_hdi_trajectory.png",
    xlim=(1990, 2023),
    ylim=(0.58, 0.83),
    note="Peers are all countries with 1990 HDI within ±0.020 of Iran's 1990 HDI (0.626), excluding Iran itself and excluding aggregates.",
)

plot_all_peers(
    undp_peer_long(hdi, "le", peer_isos),
    undp_series(hdi, "le", "IRN"),
    "Life expectancy at birth: Iran against all 14 peers",
    "Years",
    FIGURES / "02_life_expectancy.png",
    xlim=(1990, 2023),
    note="Source: UNDP HDR25 composite time series. Gray lines are peer countries; orange is the peer median; blue is Iran.",
)

u5_peers = wb_peer_long(u5_long, peer_isos)
u5_iran = wb_country(u5_long, "IRN")
u5_peers = u5_peers[u5_peers["year"] >= 2000].rename(columns={"REF_AREA": "iso3"})
u5_iran = u5_iran[u5_iran["year"] >= 2000]
u5_vals = pd.concat([u5_peers["value"], u5_iran["value"]]).dropna()
u5_upper = int(math.ceil(float(u5_vals.quantile(0.90)) / 2.0) * 2)
u5_lower = max(0, int(math.floor((float(u5_vals.min()) - 1.0) / 2.0) * 2))
u5_ylim = (u5_lower, u5_upper)
plot_all_peers(
    u5_peers,
    u5_iran,
    "Under-5 mortality: Iran against all 14 peers",
    "Deaths per 1,000 live births",
    FIGURES / "03_under5_mortality.png",
    xlim=(2000, 2023),
    ylim=u5_ylim,
    note="Source: World Bank WDI SH.DYN.MORT. Restricted to 2000–2023. Y-axis is capped at the cohort 90th percentile so central variation is visible; extreme early-year outliers are clipped.",
)

plot_all_peers(
    undp_peer_long(hdi, "mys", peer_isos),
    undp_series(hdi, "mys", "IRN"),
    "Mean years of schooling: Iran against all 14 peers",
    "Years",
    FIGURES / "04_mean_years_schooling.png",
    xlim=(1990, 2023),
    note="Source: UNDP HDR25 composite time series.",
)

plot_all_peers(
    undp_peer_long(hdi, "eys", peer_isos),
    undp_series(hdi, "eys", "IRN"),
    "Expected years of schooling: Iran against all 14 peers",
    "Years",
    FIGURES / "05_expected_years_schooling.png",
    xlim=(1990, 2023),
    note="Source: UNDP HDR25 composite time series.",
)

ter_peers = wb_peer_long(ter_long, peer_isos)
ter_iran = wb_country(ter_long, "IRN")
ter_peers = ter_peers[ter_peers["year"] >= 1990].rename(columns={"REF_AREA": "iso3"})
ter_iran = ter_iran[ter_iran["year"] >= 1990]
ter_ylim = nice_limits(pd.concat([ter_peers["value"], ter_iran["value"]]), pad_frac=0.08, zero_floor=False, step=5)
plot_all_peers(
    ter_peers,
    ter_iran,
    "Tertiary enrollment, gross: Iran against all 14 peers",
    "Percent",
    FIGURES / "06_tertiary_enrollment.png",
    xlim=(1990, 2022),
    ylim=ter_ylim,
    note="Source: World Bank Gender Statistics WB_GS_SE_TER_ENRR. Iran's series in the bundled file ends in 2020.",
)

mmr_peers = wb_peer_long(mmr_long, peer_isos)
mmr_iran = wb_country(mmr_long, "IRN")
mmr_peers = mmr_peers[mmr_peers["year"] >= 2000].rename(columns={"REF_AREA": "iso3"})
mmr_iran = mmr_iran[mmr_iran["year"] >= 2000]
mmr_ylim = nice_limits(pd.concat([mmr_peers["value"], mmr_iran["value"]]), pad_frac=0.12, zero_floor=False, step=10)
plot_all_peers(
    mmr_peers,
    mmr_iran,
    "Maternal mortality ratio: Iran against all 14 peers",
    "Per 100,000 live births",
    FIGURES / "07_maternal_mortality.png",
    xlim=(2000, 2020),
    ylim=mmr_ylim,
    note="Source: World Bank HNP WB_HNP_SH_STA_MMRT. Lower values are better. Bundled series are available through 2020.",
)

plot_rank(peer_df, hdi)

missing = [name for name in EXPECTED_FIGS if not (FIGURES / name).exists()]
if missing:
    raise SystemExit(f"Missing figures after rebuild: {missing}")

print("Done. Rebuilt", len(EXPECTED_FIGS), "figures in", FIGURES)
