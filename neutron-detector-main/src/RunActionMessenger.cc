#include "RunActionMessenger.hh"
#include "RunAction.hh"

#include "G4UIdirectory.hh"
#include "G4UIcmdWithAString.hh"
#include "G4UIcmdWithAnInteger.hh"

RunActionMessenger::RunActionMessenger(RunAction* runAction)
    : G4UImessenger(),
      fRunAction(runAction),
      fDir(nullptr),
      fPrefixCmd(nullptr),
      fOffsetCmd(nullptr)
{
    fDir = new G4UIdirectory("/analysis/");
    fDir->SetGuidance("Analysis output / checkpointing controls");

    fPrefixCmd = new G4UIcmdWithAString("/analysis/filePrefix", this);
    fPrefixCmd->SetGuidance("Output base name; each beamOn batch writes <name>_runNN.root.");
    fPrefixCmd->SetParameterName("prefix", false);
    fPrefixCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

    fOffsetCmd = new G4UIcmdWithAnInteger("/analysis/batchOffset", this);
    fOffsetCmd->SetGuidance("Batch-number offset added to the run ID (for resuming a run).");
    fOffsetCmd->SetParameterName("offset", false);
    fOffsetCmd->AvailableForStates(G4State_PreInit, G4State_Idle);
}

RunActionMessenger::~RunActionMessenger()
{
    delete fPrefixCmd;
    delete fOffsetCmd;
    delete fDir;
}

void RunActionMessenger::SetNewValue(G4UIcommand* command, G4String value)
{
    if (command == fPrefixCmd) {
        fRunAction->SetFilePrefix(value);
    } else if (command == fOffsetCmd) {
        fRunAction->SetBatchOffset(fOffsetCmd->GetNewIntValue(value));
    }
}
