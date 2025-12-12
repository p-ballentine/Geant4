#include "PhysicsList.hh"
#include "G4SystemOfUnits.hh"

PhysicsList::PhysicsList() : G4VModularPhysicsList() {
    // EM Physics
    RegisterPhysics(new G4EmStandardPhysics());

    // Radioactive decay physics
    RegisterPhysics(new G4RadioactiveDecayPhysics());

    // Decay physics
    RegisterPhysics(new G4DecayPhysics());
    
    // High precision neutron physics for thermal neutron capture
    RegisterPhysics(new G4HadronElasticPhysicsHP());
    RegisterPhysics(new G4HadronPhysicsQGSP_BERT_HP());
    RegisterPhysics(new G4NeutronTrackingCut());
}

PhysicsList::~PhysicsList() {
}

void PhysicsList::SetCuts() {
    // Set default cuts
    SetCutsWithDefault();
    
    // Set very low cuts for precise tracking of secondaries
    SetCutValue(0.1*um, "gamma");
    SetCutValue(0.1*um, "e-");
    SetCutValue(0.1*um, "e+");
    SetCutValue(0.1*um, "proton");
}