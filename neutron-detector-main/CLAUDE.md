# CLAUDE.md — Context for this repository

## What this project is

This is a GEANT4 Monte Carlo simulation of energy deposition in a thin-film
**organic semiconductor** neutron detector. The goal is to predict the
**recoil-proton energy-deposition spectrum** produced in the active organic
layer when the device is exposed to fast neutrons. That spectrum is the
physics deliverable — it is what downstream analysis uses to estimate detector
response.

This code was adapted from an earlier simulation written for III-V
semiconductor materials (GaN) with a B4C neutron converter. **That III-V/B4C
heritage is legacy.** The detector being simulated now is organic
(PEDOT:PSS / TIPS-pentacene, defined in `materials/detector-stack.json`).

## The task

Modify the simulation so the neutron source is a realistic **PuBe
(plutonium-beryllium) spectrum** instead of a single fixed energy, and produce
the **source-folded recoil-proton energy-deposition spectrum** in the active
organic layer.

Concretely:

1. **Primary generator** (`src/PrimaryGenerator.cc`): right now it fires a
   fixed monoenergetic neutron (hardcoded at 2.5 MeV). Change it to sample the
   neutron energy **per primary event** from a tabulated PuBe emission
   spectrum, so that running the simulation once produces the recoil-proton
   spectrum as the device would see it under a PuBe source. The PuBe spectrum
   should be supplied as a data table (e.g. a text file of energy-vs-relative-
   intensity); read it in and sample from it. Use the ISO 8529-1 reference PuBe
   spectrum unless told otherwise.

2. **Analysis** (`analysis/`): produce/refresh a script that reads the ROOT
   output and plots the energy-deposition spectrum in the active organic layer.
   This is the figure the project actually needs.

## Load-bearing facts — do not "correct" these away

- **The source is PuBe, not thermal, not AmBe.** The comment in
  `PrimaryGenerator.cc` that calls 2.5 MeV a "thermal neutron energy" and ties
  it to AmBe is **wrong and should be ignored/removed.** Thermal is ~0.025 eV;
  the relevant regime here is fast neutrons (roughly 1–11 MeV for PuBe).

- **The active scoring volume is the organic layer** (PEDOT:PSS or
  TIPS-pentacene, per `materials/detector-stack.json`). Energy deposition in
  the organic active layer is what matters.

- **The B4C and GaN code paths are legacy III-V scaffolding.** They can be
  ignored, and may be cleaned up if it simplifies the change, but they are not
  part of the organic detector concept. Do not build new physics around them.

- **The physics list is already correct — do not change it.**
  `src/PhysicsList.cc` uses `G4HadronElasticPhysicsHP` and
  `G4HadronPhysicsQGSP_BERT_HP` with low (0.1 µm) production cuts for protons,
  electrons, and gammas. This is the right configuration for producing and
  tracking recoil protons from elastic neutron-nucleus scattering. Leave it
  alone unless a change is explicitly requested.

- **Recoil protons come from elastic n-p scattering on hydrogen** in the
  organic material. The physics reason the organic stack works as a detector is
  its high hydrogen content. The energy a neutron can transfer to a recoil
  proton in a single elastic event is uniform on [0, E_neutron]; folding that
  over the PuBe source spectrum is the whole point of this task.

## Conventions / environment notes

- The build is standard GEANT4 + CMake:
  `mkdir build && cd build && cmake .. && make`, then `./sim macros/run.mac`.
- Output is a ROOT file; see `README.md` for the ntuple column definitions
  (StepData ntuple 0 has EnergyDeposit, position, particle name, volume name,
  process name, etc.).
- Materials are defined in `materials/detector-stack.json` and read at
  construction time; add or swap organic materials there rather than hardcoding
  them.

## Out of scope

- Carrier transport, recombination, induced charge, and readout electronics are
  **not** part of this simulation. GEANT4 gives energy deposition only; the
  conversion from deposited energy to detector signal is handled in separate
  post-processing and does not belong in this repo. Do not add it.
