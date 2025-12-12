# Semiconductor Device Simulator

Energy deposition simulation of a semiconductor device stack.


## Installation and Running

1) Install GEANT4, following the tutorial.
2) Create an alias to make GEANT4 (recommended).
3) Add the include path `path/to/GEANT4-install/include/Geant4` to the IDE settings.
4) Make a build directory and compile the project/
```
mkdir build
cd build
cmake ..
make
```
5) Run the project with `./sim [anything.mac]`, using `run.mac` in place if you don't need to use the GUI.


## Output

The ouput of the simulation is in the form of a root file. Information on what each category represents is below:

- StepData: step-by-step information
    - EventID: Unique identifier for each neutron event \
        ( event #, frequency or num entries )
    - EnergyDeposit: Energy depsoited in this specific step \
        ( energy (MeV), frequency (number of steps) ) 
    - X, Y, Z: 3D coordinates where the energy deposition occured \
        ( position (mm), requency (spatial distribution) )
    - GlobalTime: time at which step occurred \
        ( time (ns), frequency (temporal distribution) )
    - ProcessName: Physics process that caused the energy deposition
    - ParticleName: Type of particle depositing energy
    - VolumeName: Which detector volume the step occurred in
    - TrackID: 1 for primary particles (neutrons), different for others
    - ParentID: 0 for primary particles, ID of particle responsible for creation otherwise
    - KineticEnergy: KE of the particle
    - CreatorProcess: process that created the particle


## Material Definition
To define the materials in a detector, they shoulld be written in order in `detector-stack.json`.

The syntax is as follows:
```
{
    "MaterialName (i.e. GaN)" : {
        "density" : G4double representing density in g/cm3,
        "thickness" : G4double representing thickness of layer in mm,
        "composition" : {
            "Element1" : G4int representing # of Element1,
            "Element2" : G4int representing # of Element2,
            etc........
        },
        "color" : {
            "r" : G4double representing red color,
            "g" : G4double representing green color,
            "b" : G4double representing blue color,
            "a" : G4double representing alpha value
        }
    },
    "Material2" : {
        ...
    },
    etc...
}
```
