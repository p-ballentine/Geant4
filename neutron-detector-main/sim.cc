#include <iostream>

#include "G4RunManager.hh"
#include "G4MTRunManager.hh"
#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4VisManager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"

#include "PhysicsList.hh"
#include "DetectorConstruction.hh"
#include "ActionInitialization.hh"

int main(int argc, char** argv) {
    G4UIExecutive *ui = nullptr;

    // Run manager
    auto runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Default);

    // Physics list
    runManager->SetUserInitialization(new PhysicsList()); 

    // Create detector and pass to run manager
    DetectorConstruction* detector = new DetectorConstruction();
    runManager->SetUserInitialization(detector);

    // Pass detector to ActionInitialization
    runManager->SetUserInitialization(new ActionInitialization(detector));

    if (argc == 1) {
        ui = new G4UIExecutive(argc, argv);
    }

    // Initialize visulatization
    auto visManager = new G4VisExecutive(argc, argv);
    visManager->Initialize();

    // Get pointer to UI manager
    auto UImanager = G4UImanager::GetUIpointer();

    // Start UI session
    if (ui) {
        UImanager->ApplyCommand("/control/execute vis.mac");
        ui->SessionStart();
    }
    else {
        G4String command = "/control/execute ";
        G4String fileName = argv[1];
        UImanager->ApplyCommand(command + fileName);
    }

    return 0;
}
