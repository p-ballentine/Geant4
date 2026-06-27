"""
Poster figure: per-event energy DEPOSITED in the active layer (PEDOT:PSS),
overlaid for the two simulated sources (PuBe neutrons vs Cs-137 gammas).

This is energy deposited in the PEDOT:PSS *material* per primary event -- NOT a
device signal/response. It reuses existing ROOT output (no re-simulation):

  PuBe  : build/pube_100M.root   StepData, sum(EnergyDeposit) per EventID
  Cs-137: build/cs137_100M.root  over steps with VolumeName == "PEDOT_PSS"

Both histograms are normalized to unit area (probability density) so the shapes
are comparable despite very different event counts. The sparse PuBe high-energy
tail is shown as-is (no smoothing); its per-bin counts are printed to console.

A handful of events per source have per-event sums at the 1e-29 .. 1e-5 keV
level -- floating-point residuals, not physical deposits (real ionization is
>~ 10 eV). They are excluded from the log-scale display (count reported); all
other events are shown unmodified. N/mean/max are computed over the full
active-region event set (every event with deposit > 0), matching the existing
active_region_deposition_* plots.
"""
import os
import sys
import glob
import numpy as np
import uproot
import pandas as pd
import matplotlib.pyplot as plt

HERE  = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "..", "build")
ACTIVE   = "PEDOT_PSS"   # active / sense layer, scored by its real material boundary
DISP_FLOOR_KEV = 1e-2    # 10 eV: log-display floor (below = sub-physical numerical noise)

SOURCES = [
    {"key": "pube",  "name": "PuBe (neutrons)",        "legend": "PuBe (neutrons)",           "color": "crimson"},
    {"key": "cs137", "name": "Cs-137 (662 keV gamma)", "legend": r"Cs-137 (662 keV $\gamma$)", "color": "royalblue"},
]
ORIENTATIONS = {"device": "device-side (Parylene-C front)",
                "substrate": "substrate-side (PEN front)"}


def per_event_kev(src_key, orient):
    """Per-event energy deposited in PEDOT:PSS [keV], across checkpoint batches.
    Reads <src>_<orient>_runNN.root if present, else the single combined file."""
    files = sorted(glob.glob(os.path.join(BUILD, f"{src_key}_{orient}_run*.root")))
    if not files:
        single = os.path.join(BUILD, f"{src_key}_100M_{orient}.root")
        files = [single] if os.path.exists(single) else []
    if not files:
        raise SystemExit(f"No ROOT data for {src_key}/{orient} in {BUILD}.")
    out = []
    for fn in files:
        f = uproot.open(fn)
        a = f["StepData"].arrays(["EventID", "EnergyDeposit", "VolumeName"], library="np")
        vol = np.array([v.decode() if isinstance(v, bytes) else v for v in a["VolumeName"]])
        m = vol == ACTIVE
        per = pd.Series(a["EnergyDeposit"][m]).groupby(pd.Series(a["EventID"][m])).sum() * 1000.0
        out.append(per[per > 0].to_numpy())
    return np.concatenate(out) if out else np.array([])


def main():
    orient = sys.argv[1] if len(sys.argv) > 1 else "device"
    if orient not in ORIENTATIONS:
        raise SystemExit(f"Unknown orientation '{orient}'. Choose from {list(ORIENTATIONS)}.")
    for s in SOURCES:
        s["vals"] = per_event_kev(s["key"], orient)
        v = s["vals"]
        s["n"], s["mean"], s["max"] = len(v), v.mean(), v.max()
        s["n_below"] = int((v < DISP_FLOOR_KEV).sum())
        print(f"{s['name']}: N={s['n']}, mean={s['mean']:.2f} keV, max={s['max']:.1f} keV "
              f"(from {s['key']}/{orient} data, StepData PEDOT_PSS per-event sum); "
              f"{s['n_below']} events < {DISP_FLOOR_KEV*1e3:.0f} eV excluded from display")

    hi = max(s["max"] for s in SOURCES) * 1.1
    bins = np.logspace(np.log10(DISP_FLOOR_KEV), np.log10(hi), 41)

    fig, ax = plt.subplots(figsize=(7, 5))
    for s in SOURCES:
        ax.hist(s["vals"], bins=bins, density=True, histtype="step", lw=2.2,
                color=s["color"], label=f"{s['legend']}   (N={s['n']:,})")
        ax.axvline(s["mean"], color=s["color"], ls="--", lw=1.3, alpha=0.9)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Energy deposited per event in PEDOT:PSS (keV)", fontsize=11)
    ax.set_ylabel("Probability density (keV$^{-1}$)", fontsize=11)
    ax.set_title(f"Active-layer per-event energy deposition: PuBe vs Cs-137\n[{ORIENTATIONS[orient]}]",
                 fontsize=11.5)
    ax.grid(alpha=0.2, which="both")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.92)

    stat_txt = "means shown as dashed lines\n" + "\n".join(
        f"{s['name']}:  mean {s['mean']:.1f} keV,  max {s['max']:.0f} keV" for s in SOURCES)
    ax.text(0.025, 0.04, stat_txt, transform=ax.transAxes, fontsize=8, va="bottom", ha="left",
            bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.92))

    fig.text(0.5, 0.005,
             "Energy deposited in the PEDOT:PSS active material per event (not a device signal).",
             ha="center", fontsize=7, color="0.4")
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    out_path = os.path.join(HERE, f"active_layer_per_event_overlay_pube_vs_cs137_{orient}.png")
    fig.savefig(out_path, dpi=300)
    print(f"\nSaved {out_path}  (300 dpi, 7x5 in)")

    # PuBe limited-statistics tail, raw per-bin counts (shown as-is, not smoothed).
    pube = SOURCES[0]["vals"]
    counts, edges = np.histogram(pube, bins=bins)
    print("\nPuBe raw per-bin counts above 100 keV (limited-statistics tail, as displayed):")
    for i in range(len(edges) - 1):
        if edges[i] >= 100 and counts[i] > 0:
            print(f"  {edges[i]:8.1f} - {edges[i+1]:8.1f} keV : {counts[i]}")


if __name__ == "__main__":
    main()
