import uproot
import numpy as np

# Use the raw string (r"...") format that worked for you before
file_path = r"C:\Geant4Projects\neutron-detector-main-build\Release\neutron_analysis.root"

try:
    file = uproot.open(file_path)
    step_tree = file["StepData"]
    
    # Get unique list of particles and processes
    particles = np.unique(step_tree["ParticleName"].array(library="np"))
    processes = np.unique(step_tree["CreatorProcess"].array(library="np"))
    
    print("-" * 40)
    print("Particles found:", particles)
    print("-" * 40)
    print("Creator Processes found:", processes)
    print("-" * 40)

except Exception as e:
    print(f"Error reading file: {e}")