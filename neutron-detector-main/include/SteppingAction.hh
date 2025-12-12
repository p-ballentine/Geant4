#ifndef STEPPINGACTION_HH
#define STEPPINGACTION_HH

#include "G4UserSteppingAction.hh"
#include "globals.hh"

class DetectorConstruction;
class EventAction;
class G4Step;

class SteppingAction : public G4UserSteppingAction {
public:
    SteppingAction(DetectorConstruction* detector, EventAction* eventAction);
    virtual ~SteppingAction();

    virtual void UserSteppingAction(const G4Step* step) override;

private:
    DetectorConstruction* fDetectorConstruction;
    EventAction* fEventAction;
    
    // Helper methods
    G4bool IsInB4CVolume(const G4Step* step);
    G4bool IsInGaNVolume(const G4Step* step);
    G4bool IsInMaterialVolume(const G4Step* step, const G4String& materialName);
    G4String GetMaterialName(const G4Step* step);
};

#endif
