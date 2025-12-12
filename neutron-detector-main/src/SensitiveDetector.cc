#include "SensitiveDetector.hh"
#include "G4AnalysisManager.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4ThreeVector.hh"

SensitiveDetector::SensitiveDetector(const G4String& name)
    : G4VSensitiveDetector(name)
{}

SensitiveDetector::~SensitiveDetector() {}

void SensitiveDetector::Initialize(G4HCofThisEvent*) {}

void SensitiveDetector::EndOfEvent(G4HCofThisEvent*) {}

G4bool SensitiveDetector::ProcessHits(G4Step* aStep, G4TouchableHistory*) {
    // BEGIN TEST
    if (!aStep) return false;

    G4StepPoint* preStepPoint = aStep->GetPreStepPoint();
    if (!preStepPoint) return false;

    auto touchable = preStepPoint->GetTouchableHandle();
    if (!touchable) return false;

    auto volume = touchable->GetVolume();
    if (!volume) return false;
    // END TEST

    G4int eventID = G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();
    G4double energyDeposit = aStep->GetTotalEnergyDeposit();

    // G4StepPoint* preStepPoint = aStep->GetPreStepPoint();
    G4ThreeVector pos = preStepPoint->GetPosition();
    G4double globalTime = preStepPoint->GetGlobalTime();

    auto analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillNtupleIColumn(0, eventID);
    analysisManager->FillNtupleDColumn(1, energyDeposit);
    analysisManager->FillNtupleDColumn(2, pos.x());
    analysisManager->FillNtupleDColumn(3, pos.y());
    analysisManager->FillNtupleDColumn(4, pos.z());
    analysisManager->FillNtupleDColumn(5, globalTime);
    analysisManager->AddNtupleRow();

    return true;
}
