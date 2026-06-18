#ifndef PRIMARYGENERATOR_HH
#define PRIMARYGENERATOR_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"
#include <vector>

class G4ParticleGun;
class G4Event;
class PrimaryGeneratorMessenger;

// Neutron primary generator with a selectable energy distribution:
//   - Mono: fixed monoenergetic neutron (kept for validation / cross-checks)
//   - PuBe: energy sampled per event from a tabulated PuBe spectrum
// The mode and parameters are controllable at run time via /source/ macro
// commands (see PrimaryGeneratorMessenger).
class PrimaryGenerator : public G4VUserPrimaryGeneratorAction
{
public:
    enum class SourceMode { Mono, PuBe };

    PrimaryGenerator();
    virtual ~PrimaryGenerator();

    virtual void GeneratePrimaries(G4Event* event) override;

    // Configuration hooks used by the messenger.
    void SetSourceMode(SourceMode mode) { fSourceMode = mode; }
    void SetSourceMode(const G4String& name);
    void SetMonoEnergy(G4double e) { fMonoEnergy = e; }
    void SetSpectrumFile(const G4String& file);   // (re)loads immediately

private:
    G4double SampleEnergy() const;                // energy for the next primary
    void LoadSpectrum(const G4String& file);      // fills fSpecEnergy / fSpecCdf
    G4String ResolveDataPath(const G4String& file) const;

    G4ParticleGun* fParticleGun;
    PrimaryGeneratorMessenger* fMessenger;

    SourceMode fSourceMode;
    G4double   fMonoEnergy;
    G4String   fSpectrumFile;

    // Tabulated PuBe spectrum prepared for inverse-CDF sampling in energy.
    std::vector<G4double> fSpecEnergy;  // neutron energy nodes (G4 internal units)
    std::vector<G4double> fSpecCdf;     // normalized cumulative distribution [0,1]
};

#endif
