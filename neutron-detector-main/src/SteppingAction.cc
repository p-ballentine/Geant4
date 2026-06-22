#include "SteppingAction.hh"
#include "DetectorConstruction.hh"
#include "EventAction.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4StepPoint.hh"
#include "G4VProcess.hh"
#include "G4ParticleDefinition.hh"
#include "G4ParticleTypes.hh"
#include "G4RunManager.hh"
#include "G4AnalysisManager.hh"
#include "G4SystemOfUnits.hh"

SteppingAction::SteppingAction(DetectorConstruction* detector, EventAction* eventAction)
    : G4UserSteppingAction(),
      fDetectorConstruction(detector),
      fEventAction(eventAction)
{}

SteppingAction::~SteppingAction() {}

void SteppingAction::UserSteppingAction(const G4Step* step) {
    G4double edep = step->GetTotalEnergyDeposit();

    // BEGIN TEST
    if (!step) return;

    G4StepPoint* postStepPoint = step->GetPostStepPoint();
    if (!postStepPoint) return;

    auto touchable = postStepPoint->GetTouchableHandle();
    if (!touchable) return;

    auto volume = touchable->GetVolume();
    if (!volume) return;
    // END TEST

    // Get energy deposition
    // G4double edep = step->GetTotalEnergyDeposit();
    if (edep <= 0.) return;

    // Accumulate energy in appropriate detector volume
    if (IsInB4CVolume(step)) {
        fEventAction->AddB4CEnergyDeposit(edep);
    } else if (IsInGaNVolume(step)) {
        fEventAction->AddGaNEnergyDeposit(edep);
    } else {
        // Handle energy deposition in other materials
        // TODO: temp, remove all "backward compatibility" with previous GaN
        G4String materialName = GetMaterialName(step);
        if (materialName == "PEDOT_PSS" ||
            materialName == "4MHB" ||
            materialName == "4HCB" ||
            materialName == "TIPS_pentacene") {
            fEventAction->AddGaNEnergyDeposit(edep);
        }

        // TODO: track energy in other materials by extending EventAction
        // and adding material-specific energy tracking
    }

    // Get process information for analysis
    const G4VProcess* process = postStepPoint->GetProcessDefinedStep();
    
    if (!process) return;
    
    G4String processName = process->GetProcessName();
    G4String particleName = step->GetTrack()->GetParticleDefinition()->GetParticleName();
    G4String volumeName = postStepPoint->GetTouchableHandle()->GetVolume()->GetName();
    
    G4double kineticEnergy = step->GetPreStepPoint()->GetKineticEnergy();
    G4double trackLength = step->GetStepLength();

    G4int trackID = step->GetTrack()->GetTrackID();
    G4int parentID = step->GetTrack()->GetParentID();

    // Creation process for secondaries
    G4String creatorProcess = "";
    if (step->GetTrack()->GetCreatorProcess()) {
        creatorProcess = step->GetTrack()->GetCreatorProcess()->GetProcessName();
    } else {
        creatorProcess = "Primary";
    }
    
    // Fill detailed step data (ntuple 0)
    auto analysisManager = G4AnalysisManager::Instance();
    G4int eventID = G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();
    
    analysisManager->FillNtupleIColumn(0, 0, eventID);
    analysisManager->FillNtupleDColumn(0, 1, edep);
    analysisManager->FillNtupleDColumn(0, 2, postStepPoint->GetPosition().x());
    analysisManager->FillNtupleDColumn(0, 3, postStepPoint->GetPosition().y());
    analysisManager->FillNtupleDColumn(0, 4, postStepPoint->GetPosition().z());
    analysisManager->FillNtupleDColumn(0, 5, postStepPoint->GetGlobalTime());
    analysisManager->FillNtupleSColumn(0, 6, processName);
    analysisManager->FillNtupleSColumn(0, 7, particleName);
    analysisManager->FillNtupleSColumn(0, 8, volumeName);
    analysisManager->FillNtupleIColumn(0, 9, trackID);
    analysisManager->FillNtupleIColumn(0, 10, parentID);
    analysisManager->FillNtupleDColumn(0, 11, kineticEnergy);
    analysisManager->FillNtupleSColumn(0, 12, creatorProcess);
    analysisManager->AddNtupleRow(0);

}

G4bool SteppingAction::IsInB4CVolume(const G4Step* step) {
    G4LogicalVolume* volume = step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume();
    return volume == fDetectorConstruction->GetB4CLogical();
}

G4bool SteppingAction::IsInGaNVolume(const G4Step* step) {
    G4LogicalVolume* volume = step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume();
    return volume == fDetectorConstruction->GetGaNLogical();
}

G4bool SteppingAction::IsInMaterialVolume(const G4Step* step, const G4String& materialName) {
    G4LogicalVolume* volume = step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume();
    G4LogicalVolume* materialLogical = fDetectorConstruction->GetMaterialLogical(materialName);
    return volume == materialLogical;
}

G4String SteppingAction::GetMaterialName(const G4Step* step) {
    G4LogicalVolume* volume = step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume();
    
    // Check against all materials imported from JSON
    const auto& materials = fDetectorConstruction->GetDetectorMaterials();
    for (const auto& matInfo : materials) {
        if (volume == matInfo.logicalVolume) {
            return matInfo.name;
        }
    }
    
    // Check B4C
    if (volume == fDetectorConstruction->GetB4CLogical()) {
        return "B4C";
    }
    
    return "Unknown";
}
