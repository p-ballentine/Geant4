"""
Build a REPRESENTATIVE 90 kVp tungsten X-ray tube spectrum, filtered by the
0.1 mm Cu (+ Be window) recorded in the Hamamatsu L9631-15 test report
(20201112_RDS_test report). This is a physics-informed MODEL spectrum, not a
measured one -- replace with a measured/SpekCalc spectrum for quantitative work.

Model:
  - Thick-target bremsstrahlung number spectrum (Kramers): N(E) ~ (Emax - E)/E
  - Tungsten K characteristic lines (excited since 90 kV > W K-edge 69.5 keV):
      Ka2 57.98, Ka1 59.32, Kb 67.24 keV
  - Filtration: transmission through 0.1 mm Cu and ~0.2 mm Be, using tabulated
    NIST mass attenuation coefficients (log-log interpolated).

Output: data/xray_90kV_W_0p1mmCu.txt  (energy_keV  relative_intensity=dN/dE)
"""
import os
import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_TXT = os.path.join(HERE, "..", "data", "xray_90kV_W_0p1mmCu.txt")
OUT_PNG = os.path.join(HERE, "xray_90kV_source_spectrum.png")

EMAX = 90.0   # kVp
# NIST mass attenuation coefficients [cm^2/g], anchor points (>= K-edges).
CU_E  = [10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100]
CU_MU = [215, 74.1, 33.8, 10.92, 4.862, 2.613, 1.593, 1.101, 0.763, 0.581, 0.458]
BE_E  = [10, 15, 20, 30, 40, 50, 60, 80, 100]
BE_MU = [0.298, 0.148, 0.115, 0.100, 0.0946, 0.0894, 0.0850, 0.0785, 0.0736]


def mu_over_rho(E, anchorE, anchorMu):
    return np.exp(np.interp(np.log(E), np.log(anchorE), np.log(anchorMu)))


def transmission(E):
    # areal densities: 0.1 mm Cu (rho 8.96), 0.2 mm Be (rho 1.85)
    cu = mu_over_rho(E, CU_E, CU_MU) * (8.96 * 0.01)     # g/cm^2
    be = mu_over_rho(E, BE_E, BE_MU) * (1.85 * 0.02)
    return np.exp(-(cu + be))


def main():
    E = np.arange(1.0, EMAX + 0.001, 0.5)   # keV
    brem = np.where(E < EMAX, (EMAX - E) / E, 0.0)       # Kramers number spectrum
    spec = brem * transmission(E)

    # Tungsten K lines (filtered), added as narrow Gaussians. Relative line
    # weights ~ Ka1:Ka2:Kb = 100:58:30; scaled to ~18% of the continuum area.
    lines = [(57.98, 58.0), (59.32, 100.0), (67.24, 30.0)]
    kpeak = np.zeros_like(E)
    for e0, w in lines:
        kpeak += w * np.exp(-0.5 * ((E - e0) / 0.4) ** 2) * transmission(np.array([e0]))[0]
    kpeak *= 0.18 * spec.sum() / max(kpeak.sum(), 1e-9)
    spec = spec + kpeak

    spec /= spec.max()

    mean_E = np.sum(E * spec) / np.sum(spec)
    print(f"Representative 90 kVp W + 0.1mm Cu spectrum: mean photon energy {mean_E:.1f} keV, "
          f"peak near {E[np.argmax(spec)]:.0f} keV, {len(E)} points")

    os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)
    with open(OUT_TXT, "w") as f:
        f.write("# REPRESENTATIVE 90 kVp tungsten X-ray tube spectrum (MODEL, not measured)\n")
        f.write("# Source: Hamamatsu L9631-15 (W target); 90 kVp; 0.1 mm Cu + ~0.2 mm Be window\n")
        f.write("# per 20201112_RDS_test report. Kramers brem + W K-lines, NIST-attenuated.\n")
        f.write("# Col1: photon energy [keV]   Col2: relative intensity dN/dE (arbitrary)\n")
        for e, s in zip(E, spec):
            f.write(f"{e:7.2f}  {s:.6e}\n")
    print(f"Saved {OUT_TXT}")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(E, spec, color="darkred", lw=1.8)
    ax.set_xlabel("Photon energy (keV)")
    ax.set_ylabel("Relative intensity dN/dE")
    ax.set_title(f"Representative 90 kVp W tube + 0.1 mm Cu  (mean {mean_E:.0f} keV)")
    ax.set_xlim(0, 90)
    ax.grid(alpha=0.25)
    for e0, _ in lines:
        ax.axvline(e0, color="0.6", ls=":", lw=0.8)
    ax.text(0.98, 0.95, "W K-lines\n58 / 59 / 67 keV", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color="0.4")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=140)
    print(f"Saved {OUT_PNG}")


if __name__ == "__main__":
    main()
