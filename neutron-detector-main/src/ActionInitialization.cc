#include "ActionInitialization.hh"
#include "PrimaryGenerator.hh"
#include "RunAction.hh"
#include "EventAction.hh"
#include "SteppingAction.hh"
#include "DetectorConstruction.hh"

ActionInitialization::ActionInitialization(DetectorConstruction* detector)
    : G4VUserActionInitialization(),
      fDetectorConstruction(detector)
{}

ActionInitialization::~ActionInitialization()
{}

void ActionInitialization::BuildForMaster() const
{
    RunAction* runAction = new RunAction();
    SetUserAction(runAction);
}

void ActionInitialization::Build() const
{
    SetUserAction(new PrimaryGenerator());
    
    RunAction* runAction = new RunAction();
    SetUserAction(runAction);
    
    EventAction* eventAction = new EventAction(runAction);
    SetUserAction(eventAction);
    
    SteppingAction* steppingAction = new SteppingAction(fDetectorConstruction, eventAction);
    SetUserAction(steppingAction);
}
