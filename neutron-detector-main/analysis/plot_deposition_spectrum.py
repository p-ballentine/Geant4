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

ABSORBER = "PEN"   # dominant neutron-interaction volume in the FORD stack


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

    with open(OUT_GEOM, "w") as f:
        f.write(geom_text + "\n")
    print(f"Saved {OUT_GEOM}")


if __name__ == "__main__":
    main()
