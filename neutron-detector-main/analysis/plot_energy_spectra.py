import uproot
import matplotlib.pyplot as plt

file = uproot.open("../build/neutron_analysis.root")
step = file["StepData"]
edep = step["EnergyDeposit"].array(library="np")
sumnt = file["EventSummary"]
b4c_tot = sumnt["B4CEnergyDeposit"].array(library="np")
gan_tot = sumnt["GaNEnergyDeposit"].array(library="np")

# StepData
plt.figure(figsize=(6,4))
plt.hist(edep*1e3, bins=200, range=(0,3000), histtype="step", color="k")
plt.yscale('log')
plt.xlabel("Energy deposit per step (keV)")
plt.ylabel("Counts")
# plt.title("Step‐level Energy Deposition Spectrum")
plt.tight_layout()
plt.savefig("plots/energy_step_spectrum.png")

# EventSummary
plt.figure(figsize=(6,4))
plt.hist(b4c_tot*1e3, bins=100, range=(0,3000), alpha=0.6, label="B4C")
plt.hist(gan_tot*1e3, bins=100, range=(0,3000), alpha=0.6, label="GaN")
plt.yscale('log')
plt.xlabel("Total energy deposit per event (keV)")
plt.ylabel("Number of events")
# plt.title("Event‐level Energy Deposition in B4C vs GaN")
plt.legend()
plt.tight_layout()
plt.savefig("plots/energy_event_spectrum.png")

# plt.show()
