# FORD device construction memo — for Geant4 neutron simulations

**Purpose:** Provide a geometry and materials specification for a Geant4 model of the FORD (Floating Organic Radiation Detector), to study its response under neutron irradiation. All values below are drawn from the device fabrication record (Bardash US 10,923,535 B2; the CLUE-lab process-flow draft) and the project's phase-2 analysis notes. Confidence is flagged per item; treat anything marked **[UNCONFIRMED]** or **[ESTIMATE]** as a parameter to expose rather than hard-code.

> **Note:** Simulations are already underway, and much of §5–§7 below may already be reflected in the working setup. This is offered as a review pass rather than fresh instruction — flag anything that conflicts with what's already running. The neutron source is a **PuBe source (LLNL/PNL)**; the source-specific section (§5.5) and the updated physics-list and recoil notes follow from that.

---

## 1. Orientation and what matters for neutrons

The device is a layered thin-film stack on a comparatively thick polymer substrate. For the physics:

- **PEN (the substrate) is the dominant interaction volume.** It is by far the thickest layer (~125 µm vs. sub-µm for everything else) and is the proposed radiation absorber in the device mechanism. Essentially all neutron energy deposition of interest happens here.
- **For neutrons specifically, elemental composition matters more than the layer stack.** Fast-neutron energy deposition is dominated by elastic scatter off hydrogen (¹H); thermal capture proceeds mainly through ¹H(n,γ)²H (2.22 MeV gamma) and ¹⁴N(n,p)¹⁴C (in any nitrogen-bearing layer). PEN is hydrogen-rich, so it is both absorber and the main neutron interaction medium. Get the H and N content right.
- The thin functional layers (PEDOT:PSS, parylene-C, TIPS-pentacene, Au/Cr) contribute negligibly to neutron stopping but are included below for completeness and because the Au pads are the only high-Z material present (relevant if you later look at neutron-induced gammas interacting with the metal, or secondary capture in gold).

A caution worth carrying into the simulation: **PEN itself produces a gamma on thermal capture (the 2.22 MeV ¹H line), and the readout cannot distinguish a directly-deposited neutron signal from that secondary gamma.** This is the same gamma-confound issue already flagged for the Gd-doping neutron concept. Worth scoring gamma production separately from charged-particle/recoil energy deposition so the two channels can be told apart in analysis.

---

## 2. Layer stack (bottom to top)

Ordered from substrate up. Lateral extent and per-layer notes follow in §3–§4.

| # | Layer | Material | Thickness | Confidence |
|---|---|---|---|---|
| 0 | Substrate | PEN (polyethylene 2,6-naphthalate) | **125 µm [UNCONFIRMED]** | see note |
| 1 | Gate electrode / sense network | PEDOT:PSS | 116 ± 6 nm (single layer); 200–225 nm (double layer) | measured (AFM) |
| 2 | Gate metal pads | Au (100 nm) on Cr (10 nm) adhesion | 110 nm total | process spec |
| 3 | Gate dielectric | Parylene-C (PPX-C) | 450 nm (typical; 75–450 nm range achievable) | measured (AFM) |
| 4 | Source/drain electrodes (incl. active sense area) | PEDOT:PSS | ~200 nm (double layer) | measured |
| 5 | Source/drain metal pads | Au (100 nm) on Cr (10 nm) | 110 nm total | process spec |
| 6 | Semiconductor (OFET channels only) | TIPS-pentacene | ~100–500 nm (printed, non-uniform) **[ESTIMATE]** | not directly measured |

**PEN thickness note:** 125 µm is the value used throughout the phase-2 mechanism estimates (RC time constant, through-PEN field), but it is **not yet confirmed against a datasheet or caliper measurement.** The fabrication record specifies only a 50 × 50 mm laser-cut sheet, not its thickness. Standard lab PEN (DuPont Teijin Teonex Q65) ships in 50 / 75 / 100 / 125 µm. **Recommend exposing PEN thickness as a top-level parameter** so it can be swept or corrected once confirmed — for a neutron absorber this is the single most sensitive geometric input.

---

## 3. Materials definitions (for G4Material)

Elemental composition by mass fraction, which is what Geant4 wants. Build these from elements (NIST `G4_*` predefined materials exist for several and can substitute where noted).

### PEN — poly(ethylene 2,6-naphthalate)
- Chemical formula: **C₁₄H₁₀O₄** (repeat unit)
- Density: **1.36 g/cm³**
- By mass: C 68.85%, H 4.13%, O 27.02%
- NIST equivalent: no exact predefined; build by atoms per molecule (C:14, H:10, O:4). (`G4_MYLAR` = PET C₁₀H₈O₄ is a *close but not identical* polyester substitute if you need a quick stand-in — slightly different H fraction and density 1.40; prefer the explicit PEN definition.)

### PEDOT:PSS
- Mixed conducting polymer; exact stoichiometry is blend-ratio-dependent. A standard PH1000-type approximation:
- Density: **~1.0–1.5 g/cm³** (use 1.0 g/cm³ as a neutral default **[ESTIMATE]**)
- Approximate composition: C, H, O, S. A workable mass-fraction approximation for PH1000: C ~46%, H ~3%, O ~31%, S ~20% **[ESTIMATE]** — the sulfur is from the PSS sulfonate groups. Negligible for neutron stopping; precision here doesn't matter.

### Parylene-C (PPX-C)
- Chemical formula: **C₈H₇Cl** (repeat unit)
- Density: **1.289 g/cm³**
- By mass: C 69.4%, H 5.1%, Cl 25.6%
- Note the chlorine — ³⁵Cl has a non-trivial thermal neutron capture cross-section (~43 b) and a Q-value capture gamma cascade. Thin layer (450 nm), so the capture rate is tiny, but if you score capture-by-isotope it will show up.

### TIPS-pentacene (6,13-bis(triisopropylsilylethynyl)pentacene)
- Chemical formula: **C₄₄H₅₄Si₂**
- Density: **~1.1 g/cm³ [ESTIMATE]**
- By mass: C ~84.8%, H ~8.7%, Si ~6.5%
- Present only in the small OFET channel regions; negligible volume.

### Gold / Chromium pads
- Au: density 19.32 g/cm³ (`G4_Au`)
- Cr: density 7.19 g/cm³ (`G4_Cr`)
- Only high-Z material in the device. Confined to peripheral bonding pads and the source/drain/gate contacts — *not* over the active sense area. See §4 for placement.

---

## 4. Lateral geometry

### Sample and detector layout
- Full sample: **50 × 50 mm** PEN sheet, containing **8 independent detectors** (each ~10 × 10 mm). For a single-device simulation, model one 10 × 10 mm detector; the full sheet is only needed if you care about cross-talk or whole-sheet flux.
- **Active (sense) area: 2.8 × 2.8 mm** (in-lab measurement; this is the PEDOT:PSS charge-collection area between the two OFETs). This is the volume whose charge collection produces the signal.

### Feature dimensions (within one detector)
- PEDOT:PSS routing lines: **100 µm wide**
- OFET channel length: **~5 µm** (electrode spacing 5.5–9.1 µm depending on RIE time)
- OFET channel width: **~100 µm** (measured 102 ± 1 µm)
- Two OFETs flank the active area, sitting roughly at opposite edges of the 2.8 mm sense pad (exact OFET-to-active-area separation is a few hundred µm of PEDOT trace; **photomask CAD not in hand**, so treat intra-detector placement as approximate **[ESTIMATE]**).

### Gold pad placement
- Au/Cr pads are **peripheral** — bonding pads at the detector edge plus the local source/drain/gate contacts. Critically, **no gold sits over the 2.8 × 2.8 mm active sense area.** If you're modeling tissue-equivalence or low-Z signal path, the high-Z material is geometrically separated from the absorber/collector. Pad footprint dimensions are not specified in the record (the draft literally has "?? mm × ?? mm") — **[UNCONFIRMED]**, parametrize or omit for a first pass.

---

## 5. Suggested simplifications for a first-pass model

For an initial neutron-response run, a faithful but tractable geometry:

1. **PEN slab**, 10 × 10 mm × 125 µm — the absorber. Parametrize thickness.
2. **One PEDOT:PSS layer**, 2.8 × 2.8 mm × 200 nm, on top — the sense/collection region.
3. **Parylene-C layer**, 450 nm, where present (can approximate as covering the detector).
4. Skip TIPS-pentacene and the gold pads for the very first run (negligible neutron interaction; reintroduce gold if scoring neutron-induced gammas in metal).
5. Surround with the experimental medium (air, or vacuum if appropriate to the test setup).

The PEN slab alone will capture ≳99% of the neutron interaction physics. Everything else is refinement.

---

## 5.5 Source term — PuBe (LLNL/PNL)

PuBe is a fast (α,n) source driven by the ⁹Be(α,n)¹²C reaction. Key features for the source definition:

- **Neutron spectrum:** broad, ~1–11 MeV, peaking ~3–5 MeV, **mean ~4–4.5 MeV.** Same general shape as AmBe (same underlying reaction) but slightly softer and lower-yield. If a tabulated PuBe spectrum is available (ISO 8529 lists reference (α,n) spectra), use it; an AmBe spectrum is an acceptable stand-in for the shape if PuBe-specific data isn't to hand, but note the small softening.
- **Correlated 4.44 MeV gamma:** the ⁹Be(α,n)¹²C* reaction leaves ¹²C in its first excited state a large fraction of the time, which de-excites via a **4.44 MeV gamma — roughly one per neutron.** This is a *primary* gamma flux from the source itself, not a secondary capture product. **Model it explicitly.** Because FORD's readout cannot distinguish neutron-recoil signal from gamma-deposited signal, this source gamma is plausibly a larger discrimination problem than any capture gamma, and it's intrinsic to PuBe rather than incidental. Score its energy deposition separately from neutron-recoil deposition.
- **Bare vs. moderated:** a bare PuBe source keeps thermal capture (and the ¹H(n,γ) 2.22 MeV confound) as a minor channel — good for discrimination. But PuBe calibration sources are frequently housed in paraffin/water/polyethylene moderators, which thermalize the spectrum and bring the capture confound back strongly. **Confirm whether the LLNL/PNL source is bare or moderated** — it changes the recoil-vs-capture balance substantially. If moderated, the moderator must be in the geometry.
- **Geant4 setup:** `G4GeneralParticleSource` (GPS) is the natural choice — it takes an arbitrary energy histogram for the neutron spectrum directly, and a second particle definition handles the correlated 4.44 MeV gamma. (`G4ParticleGun` works but is clumsier for a continuous spectrum.) The neutron and gamma can be emitted as independent populations weighted ~1:1 unless you specifically need event-by-event correlation.

---

## 6. Scoring recommendations (neutron-specific)

- **Separate energy-deposition channels:** (a) direct charged-particle/recoil dose in PEN (proton recoils from ¹H elastic scatter — the wanted fast-neutron signal), vs. (b) secondary-gamma dose from thermal capture (¹H(n,γ), ¹⁴N(n,p) is charged so it's in channel a). The readout can't distinguish these; the simulation can and should.
- **Score capture by isotope** (¹H, ¹⁴N in PEN; ³⁵Cl in parylene; any Au capture) so the gamma-confound contribution is quantifiable.
- **Recoil proton ranges are not negligible at PuBe energies.** A 4 MeV neutron transfers up to its full energy to a proton in a head-on elastic scatter (mean ~2 MeV). A 2 MeV proton has a range of **~60–70 µm in PEN** (ρ = 1.36) — a substantial fraction of the assumed 125 µm substrate thickness. Recoil protons born in the lower half of the PEN can therefore deposit energy well away from the PEDOT sense layer, or escape the back surface entirely. **PEN thickness is a recoil-containment parameter here, not just an absorber-efficiency knob.** A fine scoring mesh through the PEN depth (not just near the sense area) is worthwhile, since *where* recoil energy lands may bear on collection efficiency, not only how much is deposited.
- Recommend **`QGSP_BIC_HP`** over `QGSP_BERT_HP` for this energy range. The binary-cascade (BIC) model handles few-MeV nucleon transport and light-ion recoils more accurately than BERT at PuBe energies; the `_HP` high-precision package remains essential for any thermalized/epithermal tail and capture below 20 MeV.

---

## 7. Open items to confirm with Peter / the lab

1. **PEN thickness** — confirm caliper (125 µm assumed, unverified). Highest-leverage unknown.
2. **PEN datasheet / grade** — confirms density (1.36 used) and exact formula; Teonex Q65 assumed.
3. **Gold pad footprint** — dimensions missing from the record.
4. **Source housing — bare vs. moderated** — the spectrum is PuBe (fast, ~4 MeV mean), but whether the LLNL/PNL source is bare or sits in a moderator determines the recoil-vs-capture balance. If moderated, the moderator geometry must be modeled. Highest-leverage source-side unknown.
5. **PEDOT:PSS density and S-content** — approximated; refine only if it turns out to matter (it shouldn't for neutron stopping).
