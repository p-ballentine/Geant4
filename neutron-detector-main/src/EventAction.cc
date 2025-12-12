#include "EventAction.hh"
#include "G4Event.hh"
#include "G4RunManager.hh"
#include "G4AnalysisManager.hh"
#include "G4SystemOfUnits.hh"

EventAction::EventAction(RunAction* runAction)
    : G4UserEventAction(),
      fRunAction(runAction),
      fB4CEnergyDeposit(0.),
      fGaNEnergyDeposit(0.)
{}

EventAction::~EventAction() {}

void EventAction::BeginOfEventAction(const G4Event*) {
    // Reset accumulators
    fB4CEnergyDeposit = 0.;
    fGaNEnergyDeposit = 0.;
}

void EventAction::EndOfEventAction(const G4Event* event) {
    // Fill event-level data to analysis manager
    auto analysisManager = G4AnalysisManager::Instance();
    G4int eventID = event->GetEventID();
    
    // Fill event summary (ntuple 1)
    analysisManager->FillNtupleIColumn(1, 0, eventID);
    analysisManager->FillNtupleDColumn(1, 1, fB4CEnergyDeposit);
    analysisManager->FillNtupleDColumn(1, 2, fGaNEnergyDeposit);
    analysisManager->AddNtupleRow(1);
    
    // Print event summary periodically
    if (eventID % 10000 == 0) {
        G4cout << "Event " << eventID 
               << ": B4C Edep = " << fB4CEnergyDeposit/keV << " keV, "
               << "GaN Edep = " << fGaNEnergyDeposit/keV << " keV" << G4endl;
    }
}
