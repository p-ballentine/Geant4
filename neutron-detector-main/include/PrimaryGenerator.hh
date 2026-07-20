#ifndef PRIMARYGENERATOR_HH
#define PRIMARYGENERATOR_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"
#include <vector>

class G4ParticleGun;
class G4Event;
class G4ParticleDefinition;
class PrimaryGeneratorMessenger;

// Primary generator with a selectable source:
//   - Mono:  fixed monoenergetic neutron (validation / cross-checks)
//   - PuBe:  neutron energy sampled per event from a tabulated PuBe spectrum
//   - Cs137: 661.7 keV monoenergetic gamma (Cs-137 gamma response)
//   - Xray:  photon energy sampled per event from a tabulated X-ray tube spectrum
// The mode and parameters are controllable at run time via /source/ macro
// commands (see PrimaryGeneratorMessenger).
class PrimaryGenerator : public G4VUserPrimaryGeneratorAction
{
public:
    enum class SourceMode { Mono, PuBe, Cs137, Xray };

    PrimaryGenerator();
    virtual ~PrimaryGenerator();

    virtual void GeneratePrimaries(G4Event* event) override;

    // Configuration hooks used by the messenger.
    void SetSourceMode(SourceMode mode) { fSourceMode = mode; }
    void SetSourceMode(const G4String& name);
    void SetMonoEnergy(G4double e) { fMonoEnergy = e; }
    void SetSpectrumFile(const G4String& file);   // (re)loads immediately

private:
    G4double SampleEnergy() const;                 // PuBe neutron energy
    G4double SampleXrayEnergy() const;             // X-ray photon energy
    void LoadSpectrum(const G4String& file);       // PuBe: fills fSpecEnergy/fSpecCdf
    void LoadXraySpectrum(const G4String& file);   // X-ray: fills fXrayEnergy/fXrayCdf
    G4String ResolveDataPath(const G4String& file) const;
    static G4double SampleFromCdf(const std::vector<G4double>& e,
                                  const std::vector<G4double>& cdf);

    G4ParticleGun* fParticleGun;
    PrimaryGeneratorMessenger* fMessenger;
    G4ParticleDefinition* fNeutron;   // cached particle definitions
    G4ParticleDefinition* fGamma;

    SourceMode fSourceMode;
    G4double   fMonoEnergy;
    G4String   fSpectrumFile;
    G4String   fXraySpectrumFile;

    // Tabulated PuBe (per-lethargy) and X-ray (dN/dE) spectra, prepared for
    // inverse-CDF sampling in energy.
    std::vector<G4double> fSpecEnergy, fSpecCdf;   // PuBe neutron
    std::vector<G4double> fXrayEnergy, fXrayCdf;   // X-ray photon
};

#endif
