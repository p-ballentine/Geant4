#include "PrimaryGenerator.hh"
#include "PrimaryGeneratorMessenger.hh"

#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4AnalysisManager.hh"
#include "Randomize.hh"

#include <fstream>
#include <sstream>
#include <vector>

PrimaryGenerator::PrimaryGenerator()
    : G4VUserPrimaryGeneratorAction(),
      fParticleGun(nullptr),
      fMessenger(nullptr),
      fNeutron(nullptr),
      fGamma(nullptr),
      fSourceMode(SourceMode::PuBe),
      fMonoEnergy(2.5*MeV),
      fSpectrumFile("data/pube_bare_LLNL_PNL_lethargy.txt")
{
    fParticleGun = new G4ParticleGun(1);

    G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
    fNeutron = particleTable->FindParticle("neutron");
    fGamma   = particleTable->FindParticle("gamma");
    fParticleGun->SetParticleDefinition(fNeutron);
    fParticleGun->SetParticleEnergy(fMonoEnergy);

    fMessenger = new PrimaryGeneratorMessenger(this);

    // Load the default PuBe spectrum so 'pube' mode works out of the box.
    LoadSpectrum(fSpectrumFile);
}

PrimaryGenerator::~PrimaryGenerator()
{
    delete fParticleGun;
    delete fMessenger;
}

void PrimaryGenerator::SetSourceMode(const G4String& name)
{
    if (name == "mono") {
        fSourceMode = SourceMode::Mono;
    } else if (name == "pube") {
        fSourceMode = SourceMode::PuBe;
    } else if (name == "cs137") {
        fSourceMode = SourceMode::Cs137;
    } else {
        G4Exception("PrimaryGenerator::SetSourceMode", "BadMode", JustWarning,
                    ("Unknown source type '" + name + "'; keeping current mode.").c_str());
    }
}

void PrimaryGenerator::SetSpectrumFile(const G4String& file)
{
    fSpectrumFile = file;
    LoadSpectrum(file);
}

G4String PrimaryGenerator::ResolveDataPath(const G4String& file) const
{
    // The executable usually runs from the build directory while the data
    // files live under the project root, so try a few relative prefixes
    // (mirrors DetectorConstruction's JSON lookup).
    const std::vector<G4String> prefixes = { "", "../", "./", "../../" };
    for (const auto& p : prefixes) {
        G4String candidate = p + file;
        std::ifstream f(candidate.c_str());
        if (f.good()) return candidate;
    }
    return file;  // fall back to the original; the caller reports the error
}

void PrimaryGenerator::LoadSpectrum(const G4String& file)
{
    G4String path = ResolveDataPath(file);
    std::ifstream in(path.c_str());
    if (!in.is_open()) {
        G4Exception("PrimaryGenerator::LoadSpectrum", "NoSpectrum", FatalException,
                    ("Could not open PuBe spectrum file: " + file).c_str());
        return;
    }

    // Read (energy [eV], fluence-per-lethargy) pairs, skipping '#' comments.
    std::vector<G4double> energy;   // G4 internal units
    std::vector<G4double> perLeth;  // column 2, arbitrary units
    G4String line;
    while (std::getline(in, line)) {
        std::size_t hash = line.find('#');
        if (hash != G4String::npos) line = line.substr(0, hash);
        std::istringstream iss(line);
        G4double e_eV, w;
        if (iss >> e_eV >> w) {
            energy.push_back(e_eV * eV);
            perLeth.push_back(w);
        }
    }
    in.close();

    if (energy.size() < 2) {
        G4Exception("PrimaryGenerator::LoadSpectrum", "BadSpectrum", FatalException,
                    ("Spectrum file has too few data points: " + path).c_str());
        return;
    }

    // Column 2 is fluence per unit lethargy (E*dPhi/dE), NOT dPhi/dE. Since
    // u = ln(E_ref/E) and du = -dE/E, the probability density in energy is
    //   dPhi/dE  proportional to  column2 / E .
    // Build a normalized cumulative distribution by trapezoidal integration of
    // that density over E; integrating (column2/E) dE is equivalent to
    // integrating column2 du, i.e. the per-lethargy weighting on the log grid.
    const std::size_t n = energy.size();
    std::vector<G4double> pdf(n);
    for (std::size_t i = 0; i < n; ++i) {
        pdf[i] = (energy[i] > 0.) ? perLeth[i] / energy[i] : 0.;
    }

    fSpecEnergy.assign(energy.begin(), energy.end());
    fSpecCdf.assign(n, 0.);
    for (std::size_t i = 1; i < n; ++i) {
        G4double dE = energy[i] - energy[i-1];
        fSpecCdf[i] = fSpecCdf[i-1] + 0.5 * (pdf[i] + pdf[i-1]) * dE;
    }

    G4double total = fSpecCdf.back();
    if (total <= 0.) {
        G4Exception("PrimaryGenerator::LoadSpectrum", "ZeroSpectrum", FatalException,
                    "PuBe spectrum integrates to zero.");
        return;
    }
    for (auto& c : fSpecCdf) c /= total;

    G4cout << "PrimaryGenerator: loaded PuBe spectrum '" << path << "' ("
           << n << " points, " << energy.front()/MeV << " - "
           << energy.back()/MeV << " MeV)." << G4endl;
}

G4double PrimaryGenerator::SampleEnergy() const
{
    if (fSourceMode == SourceMode::Mono || fSpecCdf.empty()) {
        return fMonoEnergy;
    }

    // Inverse-CDF sampling with linear interpolation within the chosen segment.
    G4double u = G4UniformRand();
    std::size_t lo = 0, hi = fSpecCdf.size() - 1;
    while (lo + 1 < hi) {
        std::size_t mid = (lo + hi) / 2;
        if (fSpecCdf[mid] <= u) lo = mid; else hi = mid;
    }
    G4double c0 = fSpecCdf[lo], c1 = fSpecCdf[hi];
    G4double e0 = fSpecEnergy[lo], e1 = fSpecEnergy[hi];
    G4double frac = (c1 > c0) ? (u - c0) / (c1 - c0) : 0.;
    return e0 + frac * (e1 - e0);
}

void PrimaryGenerator::GeneratePrimaries(G4Event* event)
{
    // Spread the source over the detector face, just above the stack, aimed +z.
    G4double x = (G4UniformRand() - 0.5) * 8*mm;
    G4double y = (G4UniformRand() - 0.5) * 8*mm;
    G4double z = -1*mm;

    // Select particle type and energy for the chosen source.
    G4ParticleDefinition* particle = fNeutron;
    G4double energy = fMonoEnergy;
    if (fSourceMode == SourceMode::Cs137) {
        particle = fGamma;
        energy = 661.7*keV;          // Cs-137 / Ba-137m gamma line
    } else if (fSourceMode == SourceMode::PuBe) {
        energy = SampleEnergy();
    }

    fParticleGun->SetParticleDefinition(particle);
    fParticleGun->SetParticlePosition(G4ThreeVector(x, y, z));
    fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0, 0, 1));
    fParticleGun->SetParticleEnergy(energy);

    // Record the source energy for spectrum validation (H1 id 0).
    G4AnalysisManager::Instance()->FillH1(0, energy/MeV);

    fParticleGun->GeneratePrimaryVertex(event);
}
