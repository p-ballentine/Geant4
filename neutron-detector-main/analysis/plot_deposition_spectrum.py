"""
PuBe source-folded energy-deposition analysis for the FORD organic neutron detector.

Produces a single summary figure with four panels:
  (A) Sampled PuBe source neutron spectrum vs. the input table  -> source validation
  (B) Energy deposited per event in the PEN absorber             -> the deliverable
  (C) Recoil-proton initial-energy spectrum (n-p elastic)        -> the physics
  (D) The actual constructed detector geometry                   -> for the record

In the FORD simplified geometry the ~125 um PEN substrate is the dominant
neutron-interaction volume; the thin PEDOT:PSS sense layer and parylene-C
deposit negligibly. So the deposition spectrum is scored in PEN.

Run from the analysis/ directory:  python plot_deposition_spectrum.py
"""
import os
import numpy as np
import uproot
import pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_FILE = os.path.join(HERE, "..", "build", "neutron_analysis.root")
GEOM_FILE = os.path.join(HERE, "..", "build", "detector_geometry.txt")
SPECTRUM  = os.path.join(HERE, "..", "data", "pube_bare_LLNL_PNL_lethargy.txt")
OUT_PNG   = os.path.join(HERE, "pube_deposition_summary.png")
OUT_GEOM  = os.path.join(HERE, "detector_geometry.txt")   # copy kept beside the figure

ABSORBER = "PEN"          # dominant neutron-interaction volume in the FORD stack
ACTIVE   = "PEDOT_PSS"    # active / sense (charge-collection) layer
LAYERS   = ["PEN", "PEDOT_PSS", "Parylene_C"]   # all detector layers, for the breakdown
SOURCE_LABEL = "PuBe (LLNL/PNL)"

# Pretty labels for figures (internal G4 volume names stay PEN / PEDOT_PSS / Parylene_C).
DISPLAY_NAMES = {"PEN": "PEN", "PEDOT_PSS": "PEDOT:PSS", "Parylene_C": "Parylene-C"}

OUT_BARS     = os.path.join(HERE, "layer_deposition_breakdown.png")
OUT_ACTIVE   = os.path.join(HERE, "active_region_deposition.png")
OUT_PEREVENT = os.path.join(HERE, "per_event_all_layers.png")

LAYER_COLORS = {"PEN": "goldenrod", "PEDOT_PSS": "navy", "Parylene_C": "seagreen"}


def load_geometry(path):
    if not os.path.exists(path):
        return "(detector_geometry.txt not found - re-run the simulation to regenerate it)"
    with open(path) as f:
        return f.read().rstrip()


def panel_source(ax, file):
    """(A) Sampled source spectrum overlaid on the input PuBe table."""
    counts, edges = file["SourceEnergy"].to_numpy()
    centers = 0.5 * (edges[:-1] + edges[1:])
    width = edges[1] - edges[0]
    ax.step(centers, counts, where="mid", color="navy", lw=1.5, label="Sampled (sim)")

    E_eV, col2 = [], []
    for line in open(SPECTRUM):
        parts = line.split("#")[0].split()
        if len(parts) == 2:
            E_eV.append(float(parts[0])); col2.append(float(parts[1]))
    E_MeV = np.array(E_eV) * 1e-6
    dNdE = np.where(E_MeV > 0, np.array(col2) / E_MeV, 0.0)   # col2 is per-lethargy
    m = (centers >= 0.5) & (centers <= 12)
    in_on_grid = np.interp(centers, E_MeV, dNdE)
    scale = counts[m].sum() / in_on_grid[m].sum() if in_on_grid[m].sum() > 0 else 1.0
    ax.plot(centers, in_on_grid * scale, color="orange", lw=2, label="Input PuBe (col2/E)")

    ax.set_title("(A) Source neutron spectrum [validation]")
    ax.set_xlabel("Neutron energy (MeV)")
    ax.set_ylabel(f"Neutrons / {width:.2f} MeV")
    ax.set_xlim(0, 12)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)


def panel_deposition(ax, step_df):
    """(B) Per-event energy deposited in the PEN absorber."""
    pen = step_df[step_df["Volume"] == ABSORBER]
    per_event = pen.groupby("EventID")["Edep"].sum()
    vals = per_event[per_event > 0].to_numpy()
    if len(vals):
        ax.hist(vals, bins=160, range=(0, 8), histtype="stepfilled",
                alpha=0.6, color="seagreen")
        ax.text(0.97, 0.95,
                f"{len(vals)} events with deposit\nmax {vals.max():.2f} MeV",
                transform=ax.transAxes, ha="right", va="top", fontsize=8)
    ax.set_yscale("log")
    ax.set_title(f"(B) Energy deposited per event in {ABSORBER} (absorber)")
    ax.set_xlabel("Energy deposited (MeV)")
    ax.set_ylabel("Events / 0.05 MeV")
    ax.grid(alpha=0.2, which="both")


def panel_recoils(ax, step_df):
    """(C) Initial energy of recoil protons from n-p elastic scattering."""
    recoils = step_df[(step_df["Particle"] == "proton") &
                      (step_df["Process"] == "hadElastic")]
    if recoils.empty:
        ax.text(0.5, 0.5, "No recoil protons found", transform=ax.transAxes,
                ha="center", va="center")
    else:
        e_mev = recoils.groupby(["EventID", "TrackID"])["KineticEnergy"].max()
        ax.hist(e_mev, bins=240, range=(0, 12), histtype="step", lw=2, color="firebrick")
        ax.text(0.97, 0.95, f"{len(e_mev)} recoil protons\nmax {e_mev.max():.1f} MeV",
                transform=ax.transAxes, ha="right", va="top", fontsize=8)
    ax.set_yscale("log")
    ax.set_title("(C) Recoil-proton initial energy (n-p elastic)")
    ax.set_xlabel("Proton energy (MeV)")
    ax.set_ylabel("Protons / 0.05 MeV")
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
    colors = ["goldenrod", "navy", "seagreen"]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    x = np.arange(len(LAYERS))
    ax.bar(x, totals, width=0.6, color=colors)
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

    fig.text(0.99, 0.01, f"{int(n_primaries):,} primaries", ha="right", fontsize=7,
             color="gray")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    print(f"Saved {out_path}")
    return dict(zip(LAYERS, totals))


def make_per_event_all_layers(step_df, out_path):
    """Per-event energy deposition for all three layers, overlaid (log-log)."""
    bins = np.logspace(-1, 4, 51)   # 0.1 keV to 10 MeV
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for L in LAYERS:
        per_event = step_df[step_df["Volume"] == L].groupby("EventID")["Edep"].sum()
        vals_kev = (per_event[per_event > 0] * 1000.0).to_numpy()
        if len(vals_kev):
            ax.hist(vals_kev, bins=bins, histtype="step", lw=2, color=LAYER_COLORS[L],
                    label=f"{DISPLAY_NAMES.get(L, L)}  ({len(vals_kev)} events)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Energy deposited per event (keV)")
    ax.set_ylabel("Events / bin")
    ax.set_title("Per-event energy deposition by layer")
    ax.legend()
    ax.grid(alpha=0.2, which="both")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    print(f"Saved {out_path}")


def make_active_region_hist(step_df, out_path):
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
        ax.hist(vals_kev, bins=nbins, range=(0, hi), histtype="stepfilled",
                alpha=0.7, color="navy")
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

    ax.set_title(f"Per-event energy deposition in active region ({label})")
    ax.set_xlabel("Energy deposited per event (keV)")
    ax.set_ylabel("Events")
    ax.grid(alpha=0.2)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    print(f"Saved {out_path} ({n} active-region events)")
    return n


def main():
    if not os.path.exists(ROOT_FILE):
        raise SystemExit(f"ROOT file not found: {ROOT_FILE}\nRun the simulation first.")
    file = uproot.open(ROOT_FILE)
    geom_text = load_geometry(GEOM_FILE)

    # Read the step ntuple once; decode the string columns.
    raw = file["StepData"].arrays(
        ["EventID", "TrackID", "EnergyDeposit", "VolumeName",
         "ParticleName", "CreatorProcess", "KineticEnergy"], library="np")
    dec = lambda a: np.array([x.decode() if isinstance(x, bytes) else x for x in a])
    step_df = pd.DataFrame({
        "EventID": raw["EventID"], "TrackID": raw["TrackID"],
        "Edep": raw["EnergyDeposit"], "Volume": dec(raw["VolumeName"]),
        "Particle": dec(raw["ParticleName"]), "Process": dec(raw["CreatorProcess"]),
        "KineticEnergy": raw["KineticEnergy"],
    })

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    panel_source(axes[0, 0], file)
    panel_deposition(axes[0, 1], step_df)
    panel_recoils(axes[1, 0], step_df)
    panel_geometry(axes[1, 1], geom_text)

    fig.suptitle("PuBe source-folded response - FORD organic neutron detector",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Saved {OUT_PNG}")

    # Layer-by-layer deposition breakdown (its own figure).
    counts, _ = file["SourceEnergy"].to_numpy()
    n_primaries = counts.sum()
    totals = make_layer_breakdown(step_df, n_primaries, SOURCE_LABEL, OUT_BARS)
    print("Layer totals (MeV):", {k: round(v, 4) for k, v in totals.items()})

    # Per-event deposition in the active (sense) layer, and all layers overlaid.
    make_active_region_hist(step_df, OUT_ACTIVE)
    make_per_event_all_layers(step_df, OUT_PEREVENT)

    with open(OUT_GEOM, "w") as f:
        f.write(geom_text + "\n")
    print(f"Saved {OUT_GEOM}")


if __name__ == "__main__":
    main()
