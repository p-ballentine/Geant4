#ifndef RUNACTIONMESSENGER_HH
#define RUNACTIONMESSENGER_HH

#include "G4UImessenger.hh"
#include "globals.hh"

class RunAction;
class G4UIdirectory;
class G4UIcmdWithAString;
class G4UIcmdWithAnInteger;

// Controls checkpointed output (each /run/beamOn batch writes its own file):
//   /analysis/filePrefix <name>   base name -> <name>_runNN.root
//   /analysis/batchOffset <N>     batch number = (run ID in this process) + N
//                                 (set this when resuming a partially-done run)
class RunActionMessenger : public G4UImessenger {
public:
    explicit RunActionMessenger(RunAction* runAction);
    virtual ~RunActionMessenger();

    virtual void SetNewValue(G4UIcommand* command, G4String value) override;

private:
    RunAction* fRunAction;
    G4UIdirectory* fDir;
    G4UIcmdWithAString* fPrefixCmd;
    G4UIcmdWithAnInteger* fOffsetCmd;
};

#endif
