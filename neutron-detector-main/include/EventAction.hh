#ifndef EVENTACTION_HH
#define EVENTACTION_HH

#include "G4UserEventAction.hh"
#include "RunAction.hh"
#include "globals.hh"

class EventAction : public G4UserEventAction {
public:
    explicit EventAction(RunAction* runAction);
    virtual ~EventAction();

    virtual void BeginOfEventAction(const G4Event* event) override;
    virtual void EndOfEventAction(const G4Event* event) override;

    // Methods to accumulate energy deposits
    void AddB4CEnergyDeposit(G4double edep) { fB4CEnergyDeposit += edep; }
    void AddGaNEnergyDeposit(G4double edep) { fGaNEnergyDeposit += edep; }

    // Get accumulated values
    G4double GetB4CEnergyDeposit() const { return fB4CEnergyDeposit; }
    G4double GetGaNEnergyDeposit() const { return fGaNEnergyDeposit; }

private:
    RunAction* fRunAction;
    
    // Energy deposit accumulators
    G4double fB4CEnergyDeposit;
    G4double fGaNEnergyDeposit;
};

#endif
