#include "RunAction.hh"
#include "RunActionMessenger.hh"
#include "G4RunManager.hh"
#include "G4Run.hh"
#include "G4AnalysisManager.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

#include <sstream>
#include <iomanip>

RunAction::RunAction()
    : G4UserRunAction(),
      fMessenger(nullptr),
      fFilePrefix("neutron_analysis"),
      fBatchOffset(0)
{
    fMessenger = new RunActionMessenger(this);

    auto analysisManager = G4AnalysisManager::Instance();
    analysisManager->SetActivation(true);
    analysisManager->SetVerboseLevel(1);
    analysisManager->SetNtupleMerging(true);

    // Create ntuple for step-by-step data
    analysisManager->CreateNtuple("StepData", "Step by step energy deposition");
    analysisManager->CreateNtupleIColumn("EventID");         // 0
    analysisManager->CreateNtupleDColumn("EnergyDeposit");   // 1
    analysisManager->CreateNtupleDColumn("X");               // 2
    analysisManager->CreateNtupleDColumn("Y");               // 3
    analysisManager->CreateNtupleDColumn("Z");               // 4
    analysisManager->CreateNtupleDColumn("GlobalTime");      // 5
    analysisManager->CreateNtupleSColumn("ProcessName");     // 6
    analysisManager->CreateNtupleSColumn("ParticleName");    // 7
    analysisManager->CreateNtupleSColumn("VolumeName");      // 8

    // Tracking charged particle creation
    analysisManager->CreateNtupleIColumn("TrackID");         // 9
    analysisManager->CreateNtupleIColumn("ParentID");        // 10
    analysisManager->CreateNtupleDColumn("KineticEnergy");   // 11
    analysisManager->CreateNtupleSColumn("CreatorProcess");  // 12
    analysisManager->FinishNtuple();

    // Create ntuple for event summary data
    analysisManager->CreateNtuple("EventSummary", "Event level summary");
    analysisManager->CreateNtupleIColumn("EventID");         // 0
    analysisManager->CreateNtupleDColumn("B4CEnergyDeposit"); // 1
    analysisManager->CreateNtupleDColumn("GaNEnergyDeposit"); // 2
    analysisManager->FinishNtuple();

    // Histogram of the sampled source neutron energy (H1 id 0), for validating
    // that the generator reproduces the input PuBe spectrum. 0-12 MeV covers
    // the fast PuBe range (peak ~3 MeV, max ~11 MeV).
    analysisManager->CreateH1("SourceEnergy", "Sampled source neutron energy (MeV)",
                              240, 0., 12.);
}

RunAction::~RunAction() {
    delete fMessenger;
}

void RunAction::BeginOfRunAction(const G4Run* run) {
    // Checkpointing: each /run/beamOn batch is one G4Run with an incrementing
    // run ID. Give each its own output file and its own deterministic seed, so
    // batches are independent, reproducible, and an interruption only costs the
    // batch in progress.
    G4int batch = run->GetRunID() + fBatchOffset;
    CLHEP::HepRandom::setTheSeed(987654321L + 1000003L * batch);

    std::ostringstream fn;
    fn << fFilePrefix << "_run" << std::setw(2) << std::setfill('0') << batch << ".root";

    auto analysisManager = G4AnalysisManager::Instance();
    analysisManager->SetFileName(fn.str());
    analysisManager->OpenFile();
    G4cout << "RunAction: batch " << batch << " -> " << fn.str() << G4endl;
}

void RunAction::EndOfRunAction(const G4Run*) {
    auto analysisManager = G4AnalysisManager::Instance();
    analysisManager->Write();
    analysisManager->CloseFile();
}
