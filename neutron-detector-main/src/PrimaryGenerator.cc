#include "PrimaryGenerator.hh"

#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4RandomDirection.hh"
#include "Randomize.hh"

PrimaryGenerator::PrimaryGenerator()
    : G4VUserPrimaryGeneratorAction(),
      fParticleGun(nullptr),
      fThermalNeutronEnergy(2.5*MeV)  // Standard thermal neutron energy is 0.025*eV, 2.5*MeV is about peak flux for AmBe neutron source
{
    fParticleGun = new G4ParticleGun(1);
    
    // Set thermal neutron as the particle
    G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
    G4ParticleDefinition* neutron = particleTable->FindParticle("neutron");
    fParticleGun->SetParticleDefinition(neutron);
    fParticleGun->SetParticleEnergy(fThermalNeutronEnergy);
}

PrimaryGenerator::~PrimaryGenerator()
{
    delete fParticleGun;
}

void PrimaryGenerator::GeneratePrimaries(G4Event* event)
{
    // Position source above the detector (1 mm above B4C layer)
    G4double x = (G4UniformRand() - 0.5) * 8*mm;  // Spread source over detector area
    G4double y = (G4UniformRand() - 0.5) * 8*mm;
    // G4double x = 0;
    // G4double y = 0;
    G4double z = -1*mm;  // Position above detector
    
    fParticleGun->SetParticlePosition(G4ThreeVector(x, y, z));
    
    // Set downward direction (towards detector)
    fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0, 0, 1));

    fParticleGun->GeneratePrimaryVertex(event);
}
