"""
Energy-deposition analysis for the FORD organic detector, for a selectable source.

Usage:
    python plot_deposition_spectrum.py [pube|cs137]      (default: pube)

Reads the per-source ROOT file (build/<source>_100M.root) and writes a set of
source-suffixed figures:
    deposition_summary_<src>.png            4-panel overview
    layer_deposition_breakdown_<src>.png    total energy per layer (3 bars)
    per_event_all_layers_<src>.png          per-event deposition, all layers
    active_region_deposition_<src>.png      per-event deposition in PEDOT:PSS

The ~125 um PEN substrate is the dominant interaction volume for both the PuBe
neutrons (recoil protons) and the Cs-137 gammas (Compton/photo electrons); the
thin PEDOT:PSS sense layer and parylene-C deposit much less.
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
GEOM_FILE = os.path.join(BUILD, "detector_geometry.txt")
SPECTRUM  = os.path.join(HERE, "..", "data", "pube_bare_LLNL_PNL_lethargy.txt")

ABSORBER = "PEN"          # dominant interaction volume in the FORD stack
ACTIVE   = "PEDOT_PSS"    # active / sense (charge-collection) layer
LAYERS   = ["PEN", "PEDOT_PSS", "Parylene_C"]
DISPLAY_NAMES = {"PEN": "PEN", "PEDOT_PSS": "PEDOT:PSS", "Parylene_C": "Parylene-C"}
LAYER_COLORS  = {"PEN": "goldenrod", "PEDOT_PSS": "navy", "Parylene_C": "seagreen"}
# Poster colors for the per-event overlay figure only (per_event_all_layers_*).
PEREVENT_COLORS = {"PEN": "black", "PEDOT_PSS": "#558ED5", "Parylene_C": "gray"}

SOURCES = {
    "pube":  {"label": "PuBe (LLNL/PNL)",        "overlay_spectrum": True,  "source_xlim": (0, 12)},
    "cs137": {"label": "Cs-137 (662 keV gamma)", "overlay_spectrum": False, "source_xlim": (0, 1.5)},
    "xray":  {"label": "X-ray (90 kVp W + 0.1mm Cu)", "overlay_spectrum": False, "source_xlim": (0, 0.1)},
}
# Irradiation orientation: which face of the stack the beam enters first.
ORIENTATIONS = {
    "device":    "device-side (Parylene-C front)",   # Parylene -> PEDOT -> PEN
    "substrate": "substrate-side (PEN front)",       # PEN -> PEDOT -> Parylene (device flipped)
}


def out(name, src, orient):
    return os.path.join(HERE, f"{name}_{src}_{orient}.png")


def load_geometry(path):
    if not os.path.exists(path):
        return "(detector_geometry.txt not found - re-run the simulation)"
    with open(path) as f:
        return f.read().rstrip()


def resolve_inputs(src, orient):
    """Return the ROOT file(s) for a (source, orientation): checkpoint batch
    files (<src>_<orient>_runNN.root) if present, else a single combined file."""
    batch = sorted(glob.glob(os.path.join(BUILD, f"{src}_{orient}_run*.root")))
    if batch:
        return batch
    single = os.path.join(BUILD, f"{src}_100M_{orient}.root")
    return [single] if os.path.exists(single) else []


def load_data(files):
    """Read StepData + SourceEnergy from one or more files. Event IDs are offset
    per file so events from different batches stay distinct; the source histogram
    is summed across files."""
    cols = ["EventID", "TrackID", "EnergyDeposit", "VolumeName",
            "ParticleName", "CreatorProcess", "KineticEnergy"]
    dec = lambda a: np.array([x.decode() if isinstance(x, bytes) else x for x in a])
    frames, h1c, h1e, offset = [], None, None, 0
    for fn in files:
        f = uproot.open(fn)
        raw = f["StepData"].arrays(cols, library="np")
        eid = raw["EventID"]
        frames.append(pd.DataFrame({
            "EventID": eid + offset, "TrackID": raw["TrackID"],
            "Edep": raw["EnergyDeposit"], "Volume": dec(raw["VolumeName"]),
            "Particle": dec(raw["ParticleName"]), "Process": dec(raw["CreatorProcess"]),
            "KineticEnergy": raw["KineticEnergy"],
        }))
        c, h1e = f["SourceEnergy"].to_numpy()
        h1c = c if h1c is None else h1c + c
        offset += (int(eid.max()) + 1) if len(eid) else 0
    return pd.concat(frames, ignore_index=True), h1c, h1e


def panel_source(ax, counts, edges, cfg):
    """(A) Sampled source spectrum (overlaid on the input table for PuBe)."""
    centers = 0.5 * (edges[:-1] + edges[1:])
    width = edges[1] - edges[0]
    ax.step(centers, counts, where="mid", color="navy", lw=1.5, label="Sampled (sim)")
    if cfg["overlay_spectrum"]:
        E_eV, col2 = [], []
        for line in open(SPECTRUM):
            parts = line.split("#")[0].split()
            if len(parts) == 2:
                E_eV.append(float(parts[0])); col2.append(float(parts[1]))
        E_MeV = np.array(E_eV) * 1e-6
        dNdE = np.where(E_MeV > 0, np.array(col2) / E_MeV, 0.0)   # col2 is per-lethargy
        m = (centers >= 0.5) & (centers <= 12)
        grid = np.interp(centers, E_MeV, dNdE)
        scale = counts[m].sum() / grid[m].sum() if grid[m].sum() > 0 else 1.0
        ax.plot(centers, grid * scale, color="orange", lw=2, label="Input table (col2/E)")
    ax.set_title("(A) Source spectrum [validation]")
    ax.set_xlabel("Primary energy (MeV)")
    ax.set_ylabel(f"Primaries / {width:.2f} MeV")
    ax.set_xlim(*cfg["source_xlim"])
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)


def panel_deposition(ax, step_df):
    """(B) Per-event energy deposited in the PEN absorber."""
    pen = step_df[step_df["Volume"] == ABSORBER]
    per_event = pen.groupby("EventID")["Edep"].sum()
    vals = per_event[per_event > 0].to_numpy()
    if len(vals):
        ax.hist(vals, bins=160, range=(0, 8), histtype="stepfilled", alpha=0.6, color="seagreen")
        ax.text(0.97, 0.95, f"{len(vals)} events with deposit\nmax {vals.max():.2f} MeV",
                transform=ax.transAxes, ha="right", va="top", fontsize=8)
    ax.set_yscale("log")
    ax.set_title(f"(B) Energy deposited per event in {ABSORBER} (absorber)")
    ax.set_xlabel("Energy deposited (MeV)")
    ax.set_ylabel("Events / 0.05 MeV")
    ax.grid(alpha=0.2, which="both")


def panel_secondary(ax, step_df):
    """(C) Recoil protons (neutron source) or knock-on electrons (gamma source)."""
    protons = step_df[(step_df["Particle"] == "proton") & (step_df["Process"] == "hadElastic")]
    if not protons.empty:
        e = protons.groupby(["EventID", "TrackID"])["KineticEnergy"].max()
        ax.hist(e, bins=240, range=(0, 12), histtype="step", lw=2, color="firebrick")
        ax.set_title("(C) Recoil-proton initial energy (n-p elastic)")
        ax.set_xlabel("Proton energy (MeV)")
        ax.text(0.97, 0.95, f"{len(e)} recoil protons", transform=ax.transAxes,
                ha="right", va="top", fontsize=8)
    else:
        electrons = step_df[step_df["Particle"] == "e-"]
        if not electrons.empty:
            e = electrons.groupby(["EventID", "TrackID"])["KineticEnergy"].max() * 1000.0
            ax.hist(e, bins=120, range=(0, 700), histtype="step", lw=2, color="firebrick")
            ax.set_title("(C) Secondary-electron initial energy")
            ax.set_xlabel("Electron energy (keV)")
            ax.text(0.97, 0.95, f"{len(e)} electrons", transform=ax.transAxes,
                    ha="right", va="top", fontsize=8)
        else:
            ax.text(0.5, 0.5, "no charged secondaries", transform=ax.transAxes, ha="center")
            ax.set_title("(C) Secondary particles")
    ax.set_yscale("log")
    ax.set_ylabel("Tracks / bin")
    ax.grid(alpha=0.2, which="both")


def panel_geometry(ax, geom_text):
    """(D) The constructed geometry, as recorded by the simulation."""
    ax.axis("off")
    ax.set_title("(D) Detector geometry (as built)")
    ax.text(0.0, 1.0, geom_text, transform=ax.transAxes, ha="left", va="top",
            family="monospace", fontsize=7)


def make_layer_breakdown(step_df, n_primaries, source_label, out_path):
    """Bar chart of total energy deposited in each detector layer."""
    totals = [float(step_df.loc[step_df["Volume"] == L, "Edep"].sum()) for L in LAYERS]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    x = np.arange(len(LAYERS))
    ax.bar(x, totals, width=0.6, color=[LAYER_COLORS[L] for L in LAYERS])
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([DISPLAY_NAMES.get(L, L) for L in LAYERS])
    ax.set_ylabel("Total energy deposited (MeV)")
    ax.set_title(f"Layer-by-layer energy deposition - {source_label}")
    ax.grid(axis="y", alpha=0.3, which="both")
    ax.set_axisbelow(True)

    top = max(totals) if max(totals) > 0 else 1.0
    floor = top * 1e-4
    for xi, v in zip(x, totals):
        per = (v / n_primaries * 1e3) if n_primaries else 0.0  # keV per primary
        ax.text(xi, max(v, floor), f"  {v:.4g} MeV\n  {per:.3g} keV/primary",
                ha="center", va="bottom", fontsize=8.5)
    ax.set_ylim(floor, top * 5)

    fig.text(0.99, 0.01, f"{int(n_primaries):,} primaries", ha="right", fontsize=7, color="gray")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    print(f"Saved {out_path}")
    return dict(zip(LAYERS, totals))


def make_per_event_all_layers(step_df, source_label, out_path):
    """Per-event energy deposition for all three layers, overlaid (log-log)."""
    bins = np.logspace(-1, 4, 51)   # 0.1 keV to 10 MeV
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for L in LAYERS:
        per_event = step_df[step_df["Volume"] == L].groupby("EventID")["Edep"].sum()
        vals_kev = (per_event[per_event > 0] * 1000.0).to_numpy()
        if len(vals_kev):
            ax.hist(vals_kev, bins=bins, histtype="step", lw=2, color=PEREVENT_COLORS[L],
                    label=DISPLAY_NAMES.get(L, L))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Energy deposited per event (keV)")
    ax.set_ylabel("Events / bin")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.2, which="both")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    print(f"Saved {out_path}")


def make_active_region_hist(step_df, source_label, out_path):
    """Per-event energy deposited in the active (sense) layer."""
    label = DISPLAY_NAMES.get(ACTIVE, ACTIVE)
    act = step_df[step_df["Volume"] == ACTIVE]
    per_event = act.groupby("EventID")["Edep"].sum()
    vals_kev = (per_event[per_event > 0] * 1000.0).to_numpy()   # keV (deposits are small)
    n = len(vals_kev)

    fig, ax = plt.subplots(figsize=(7, 5))
    if n > 0:
        hi = max(20.0, float(np.percentile(vals_kev, 99)))
        nbins = int(np.clip(n // 10, 10, 50))   # avoid over-binning sparse data
        ax.hist(vals_kev, bins=nbins, range=(0, hi), histtype="stepfilled", alpha=0.7, color="navy")
        ax.text(0.97, 0.95,
                f"{n} events with deposit\nmean {vals_kev.mean():.1f} keV\nmax {vals_kev.max():.1f} keV",
                transform=ax.transAxes, ha="right", va="top", fontsize=9)
        if n < 500:
            ax.text(0.5, 0.5, "LOW STATISTICS\n(few active-layer events)",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=13, color="firebrick", alpha=0.35, rotation=20)
    else:
        ax.text(0.5, 0.5, "no deposition in active region",
                transform=ax.transAxes, ha="center", va="center")

    ax.set_title(f"Per-event deposition in active region ({label}) - {source_label}")
    ax.set_xlabel("Energy deposited per event (keV)")
    ax.set_ylabel("Events")
    ax.grid(alpha=0.2)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    print(f"Saved {out_path} ({n} active-region events)")
    return n


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "pube"
    orient = sys.argv[2] if len(sys.argv) > 2 else "device"
    if src not in SOURCES:
        raise SystemExit(f"Unknown source '{src}'. Choose from {list(SOURCES)}.")
    if orient not in ORIENTATIONS:
        raise SystemExit(f"Unknown orientation '{orient}'. Choose from {list(ORIENTATIONS)}.")
    cfg = SOURCES[src]
    files = resolve_inputs(src, orient)
    if not files:
        raise SystemExit(f"No ROOT data for {src}/{orient} in {BUILD}.\nRun the simulation first.")
    label = f"{cfg['label']}, {ORIENTATIONS[orient]}"
    print(f"Source: {src}/{orient} ({label})  <-  {len(files)} file(s)")

    step_df, h1_counts, h1_edges = load_data(files)
    geom_text = load_geometry(os.path.join(BUILD, f"detector_geometry_{orient}.txt"))

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    panel_source(axes[0, 0], h1_counts, h1_edges, cfg)
    panel_deposition(axes[0, 1], step_df)
    panel_secondary(axes[1, 0], step_df)
    panel_geometry(axes[1, 1], geom_text)
    fig.suptitle(f"{label} response - FORD organic detector", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    summary_path = out("deposition_summary", src, orient)
    fig.savefig(summary_path, dpi=130)
    print(f"Saved {summary_path}")

    n_primaries = h1_counts.sum()
    totals = make_layer_breakdown(step_df, n_primaries, label, out("layer_deposition_breakdown", src, orient))
    print("Layer totals (MeV):", {k: round(v, 4) for k, v in totals.items()})
    make_active_region_hist(step_df, label, out("active_region_deposition", src, orient))
    make_per_event_all_layers(step_df, label, out("per_event_all_layers", src, orient))

    geom_copy = os.path.join(HERE, f"detector_geometry_{orient}.txt")
    with open(geom_copy, "w") as f:
        f.write(geom_text + "\n")
    print(f"Saved {geom_copy}")


if __name__ == "__main__":
    main()
