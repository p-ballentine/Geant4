#ifndef PRIMARYGENERATORMESSENGER_HH
#define PRIMARYGENERATORMESSENGER_HH

#include "G4UImessenger.hh"
#include "globals.hh"

class PrimaryGenerator;
class G4UIdirectory;
class G4UIcmdWithAString;
class G4UIcmdWithADoubleAndUnit;

// UI messenger exposing the neutron source configuration under /source/:
//   /source/type mono|pube       select the energy distribution
//   /source/monoEnergy <E> <unit> set the monoenergetic energy (mono mode)
//   /source/spectrumFile <path>   load a PuBe spectrum table (pube mode)
class PrimaryGeneratorMessenger : public G4UImessenger
{
public:
    explicit PrimaryGeneratorMessenger(PrimaryGenerator* generator);
    virtual ~PrimaryGeneratorMessenger();

    virtual void SetNewValue(G4UIcommand* command, G4String value) override;

private:
    PrimaryGenerator* fGenerator;
    G4UIdirectory* fDir;
    G4UIcmdWithAString* fTypeCmd;
    G4UIcmdWithADoubleAndUnit* fMonoCmd;
    G4UIcmdWithAString* fFileCmd;
};

#endif
