#ifndef PRIMARYGENERATOR_HH
#define PRIMARYGENERATOR_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ParticleGun.hh"
#include "globals.hh"

class G4ParticleGun;
class G4Event;

class PrimaryGenerator : public G4VUserPrimaryGeneratorAction
{
public:
    PrimaryGenerator();
    virtual ~PrimaryGenerator();
    
    virtual void GeneratePrimaries(G4Event* event) override;
    
private:
    G4ParticleGun* fParticleGun;
    G4double fThermalNeutronEnergy;
};

#endif
