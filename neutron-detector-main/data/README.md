# Source neutron-energy spectra

Tabulated neutron **emission spectra** for the radionuclide source the
simulation samples from per primary event (see `src/PrimaryGenerator.cc`).
These are *source* data — distinct from the detector *materials* in
`../materials/`.

## Files

| File | Source | Notes |
|------|--------|-------|
| `pube_bare_LLNL_PNL_lethargy.txt` | IAEA TRS-403, Table 4.XI (LLNL/PNL) | **Primary.** Bare ²³⁸Pu-Be source; less room-scatter distortion. |
| `pube_CERN_1m_lethargy.txt` | IAEA TRS-403, Table 4.X (CERN) | Alternate, measured at 1 m. For comparison/cross-check. |

Both are authoritative, citable PuBe spectra from the IAEA "Compendium of
Neutron Spectra and Detector Responses for Radiation Protection Purposes"
(TRS-403). The simulation uses the **LLNL/PNL** table by default.

## File format

Plain text, two whitespace-separated columns; `#` lines are comments:

```
# Col1: Energy [eV]   Col2: fluence per lethargy E*dPhi/dE [relative units]
1.000000e+06  1.200000e-01
...
```

- **Column 1 — energy, in eV** (note: eV, *not* MeV). Ascending, on a
  logarithmic grid spanning thermal (~1e-3 eV) to fast (~few×1e7 eV).
- **Column 2 — fluence per unit lethargy**, `E·dΦ/dE`, in arbitrary relative
  units. This is a per-bin probability weight on the log-energy grid. Absolute
  scale is irrelevant (the loader normalizes); only the shape matters.

## ⚠️ Column 2 is per *lethargy*, not per energy — read before sampling

Lethargy is `u = ln(E_ref / E)`, so `du = -dE / E`. Therefore

```
column2  =  dΦ/du  =  E · dΦ/dE          ⇒   dΦ/dE  ∝  column2 / E
```

To sample a neutron energy per event correctly you must **not** treat column 2
as `dΦ/dE`. Two equivalent correct approaches:

1. **Per-bin (lethargy) sampling:** pick a grid bin with probability
   proportional to `column2 × Δu`, where `Δu` is the bin's lethargy width
   (`Δu ≈ ln(E_{i+1}/E_{i-1})/2`). On a perfectly equilethargy grid Δu is
   constant and the weight reduces to column 2 itself — but these grids are
   *not* uniformly equilethargy, so include Δu.
2. **Per-energy PDF:** build `dΦ/dE ∝ column2 / E` and inverse-CDF sample in E.

Sampling proportional to column 2 in *linear energy* would over-weight high
energies by a factor of E and badly distort the spectrum.

The generator handles eV→MeV conversion and this lethargy weighting internally;
keep these files in their original authoritative form (eV, per-lethargy).

## Provenance note

ISO 8529-1 does **not** define a PuBe reference spectrum (its radionuclide
fields are ²⁵²Cf, ²⁵²Cf/D₂O, and ²⁴¹Am-Be). The authoritative PuBe data used
here are from IAEA TRS-403 (LLNL/PNL and CERN tabulations).
