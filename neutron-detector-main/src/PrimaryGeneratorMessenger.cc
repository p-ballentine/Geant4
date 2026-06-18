#include "PrimaryGeneratorMessenger.hh"
#include "PrimaryGenerator.hh"

#include "G4UIdirectory.hh"
#include "G4UIcmdWithAString.hh"
#include "G4UIcmdWithADoubleAndUnit.hh"

PrimaryGeneratorMessenger::PrimaryGeneratorMessenger(PrimaryGenerator* generator)
    : G4UImessenger(),
      fGenerator(generator),
      fDir(nullptr),
      fTypeCmd(nullptr),
      fMonoCmd(nullptr),
      fFileCmd(nullptr)
{
    fDir = new G4UIdirectory("/source/");
    fDir->SetGuidance("Neutron source configuration");

    fTypeCmd = new G4UIcmdWithAString("/source/type", this);
    fTypeCmd->SetGuidance("Select the source energy distribution: 'mono' or 'pube'.");
    fTypeCmd->SetParameterName("type", false);
    fTypeCmd->SetCandidates("mono pube");
    fTypeCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

    fMonoCmd = new G4UIcmdWithADoubleAndUnit("/source/monoEnergy", this);
    fMonoCmd->SetGuidance("Set the monoenergetic neutron energy (used in 'mono' mode).");
    fMonoCmd->SetParameterName("E", false);
    fMonoCmd->SetUnitCategory("Energy");
    fMonoCmd->SetDefaultUnit("MeV");
    fMonoCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

    fFileCmd = new G4UIcmdWithAString("/source/spectrumFile", this);
    fFileCmd->SetGuidance("Path to the PuBe spectrum table (energy in eV, fluence per lethargy).");
    fFileCmd->SetParameterName("file", false);
    fFileCmd->AvailableForStates(G4State_PreInit, G4State_Idle);
}

PrimaryGeneratorMessenger::~PrimaryGeneratorMessenger()
{
    delete fTypeCmd;
    delete fMonoCmd;
    delete fFileCmd;
    delete fDir;
}

void PrimaryGeneratorMessenger::SetNewValue(G4UIcommand* command, G4String value)
{
    if (command == fTypeCmd) {
        fGenerator->SetSourceMode(value);
    } else if (command == fMonoCmd) {
        fGenerator->SetMonoEnergy(fMonoCmd->GetNewDoubleValue(value));
    } else if (command == fFileCmd) {
        fGenerator->SetSpectrumFile(value);
    }
}
