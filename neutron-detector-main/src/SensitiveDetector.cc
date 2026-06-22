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

    // The StepData ntuple is populated by SteppingAction for energy-depositing
    // steps, with full per-step information (volume, particle, process, etc.).
    // Filling it here for every hit -- including the many zero-deposit transit
    // steps through the sensitive volumes -- duplicated those rows and bloated
    // the output enormously (~96% of rows, ~20x the file size at high statistics)
    // without adding anything the analysis uses. This sensitive detector is kept
    // attached (so the layers are registered as sensitive) but no longer writes
    // to the ntuple.
    return true;
}
