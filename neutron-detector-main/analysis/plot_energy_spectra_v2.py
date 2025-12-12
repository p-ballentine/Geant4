import uproot
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. Load the ROOT file
# Adjust the path if your build folder is named differently
file_path = r"C:\Geant4Projects\neutron-detector-main-build\Release\neutron_analysis.root"

try:
    file = uproot.open(file_path)
except FileNotFoundError:
    print(f"Error: Could not find file at {file_path}")
    print("Please check the path to your .root file.")
    exit()

# ---------------------------------------------------------
# PLOT 1: Total Energy Deposited per Event (Pulse Height Spectrum)
# ---------------------------------------------------------
print("Processing Total Energy Deposition...")

summary_tree = file["EventSummary"]
# In your modified code, "GaNEnergyDeposit" accumulates the energy for your 
# active organic layer (PEDOT:PSS, 4MHB, etc.)
total_edep_mev = summary_tree["GaNEnergyDeposit"].array(library="np")

# Convert to keV
total_edep_kev = total_edep_mev * 1000

plt.figure(figsize=(8, 6))
plt.hist(total_edep_kev, bins=200, range=(0, 2000), 
         histtype='stepfilled', alpha=0.6, color='blue', label='Organic Layer')

plt.yscale('log')
plt.xlabel("Total Energy Deposited (keV)")
plt.ylabel("Counts")
plt.title("Total Energy Deposition Spectrum")
plt.legend()
plt.grid(True, which="both", ls="-", alpha=0.2)
plt.tight_layout()
plt.savefig("plot_total_energy_deposition.png")
print("Saved plot_total_energy_deposition.png")


# ---------------------------------------------------------
# PLOT 2: Recoil Proton Energy Spectrum
# ---------------------------------------------------------
print("Processing Recoil Proton Spectrum...")

step_tree = file["StepData"]

# Load only necessary columns to save memory
keys = ["ParticleName", "CreatorProcess", "KineticEnergy", "TrackID", "EventID"]
data = step_tree.arrays(keys, library="np")

# Create a DataFrame for easier filtering
df = pd.DataFrame({
    "EventID": data["EventID"],
    "TrackID": data["TrackID"],
    "Particle": data["ParticleName"],
    "Process": data["CreatorProcess"],
    "Energy": data["KineticEnergy"]
})

# Filter 1: Select only Protons
# Filter 2: Select only protons created by Elastic Scattering ("hadElastic")
recoil_protons = df[
    (df["Particle"] == "proton") & 
    (df["Process"] == "hadElastic")
]

if recoil_protons.empty:
    print("Warning: No recoil protons found! Check if physics list (HP) is active or beam energy is sufficient.")
else:
    # Group by unique particles (EventID + TrackID)
    # A single particle has multiple steps. We want its INITIAL energy.
    # Since we set SteppingAction to record PreStepPoint energy, the Maximum energy 
    # recorded for a track is effectively its starting energy.
    unique_proton_energies = recoil_protons.groupby(["EventID", "TrackID"])["Energy"].max()

    # Convert to keV
    proton_energies_kev = unique_proton_energies * 1000

    plt.figure(figsize=(8, 6))
    plt.hist(proton_energies_kev, bins=200, range=(0, 2000), 
             histtype='step', linewidth=2, color='red', label='Recoil Protons')

    plt.yscale('log')
    plt.xlabel("Recoil Proton Energy (keV)")
    plt.ylabel("Counts")
    plt.title("Recoil Proton Initial Energy Spectrum")
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.tight_layout()
    plt.savefig("plot_recoil_proton_spectrum.png")
    print(f"Saved plot_recoil_proton_spectrum.png ({len(unique_proton_energies)} protons found)")