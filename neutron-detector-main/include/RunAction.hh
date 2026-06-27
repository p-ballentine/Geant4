#ifndef RUNACTION_HH
#define RUNACTION_HH

#include "G4UserRunAction.hh"
#include "globals.hh"

class G4Run;
class RunActionMessenger;

class RunAction : public G4UserRunAction {
public:
    RunAction();
    virtual ~RunAction();

    virtual void BeginOfRunAction(const G4Run*) override;
    virtual void EndOfRunAction(const G4Run*) override;

    // Checkpointing controls (set via /analysis/ macro commands). Each
    // /run/beamOn batch writes its own file <prefix>_run<NN>.root with its own
    // deterministic seed, so an interruption only loses the in-progress batch.
    void SetFilePrefix(const G4String& p) { fFilePrefix = p; }
    void SetBatchOffset(G4int n) { fBatchOffset = n; }

private:
    RunActionMessenger* fMessenger;
    G4String fFilePrefix;   // output base name -> <prefix>_runNN.root
    G4int    fBatchOffset;  // added to this process's run ID (for resuming)
};

#endif
