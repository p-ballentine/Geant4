#include "DetectorConstruction.hh"
#include "SensitiveDetector.hh"

#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4LogicalCrystalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4NistManager.hh"
#include "G4Element.hh"
#include "G4Isotope.hh"
#include "G4Material.hh"
#include "G4ExtendedMaterial.hh"
#include "G4CrystalExtension.hh"
#include "G4CrystalUnitCell.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"
#include "G4SDManager.hh"
#include <memory>
#include <fstream>
#include <iostream>
#include <sstream>
#include <algorithm>
#include <vector>

DetectorConstruction::DetectorConstruction()
    : G4VUserDetectorConstruction(),
    fB4CMaterial(nullptr),
    fGaNMaterial(nullptr),
    fWorldMaterial(nullptr),
    fB4CLogical(nullptr),
    fGaNLogical(nullptr),
    fTotalDetectorThickness(0.0),
    fWorldSizeXY(1.2 * cm),     // Updated to 1.2 cm as requested
    fWorldSizeZ(1.2 * cm),
    fB4CThickness(0.0),       // B4C thickness set to 0
    fGaNThickness(0.0)
{
    DefineMaterials();
}

DetectorConstruction::~DetectorConstruction()
{
}

void DetectorConstruction::DefineMaterials()
{
    G4NistManager* nist = G4NistManager::Instance();

    // World material (vacuum)
    fWorldMaterial = nist->FindOrBuildMaterial("G4_Galactic");

    // Load materials from JSON
    LoadMaterialsFromJSON();

    G4cout << *(G4Material::GetMaterialTable()) << G4endl;
}

void DetectorConstruction::LoadMaterialsFromJSON()
{
    std::ifstream jsonFile;
    std::string foundPath = "";

    // Try multiple possible locations for the JSON file
    std::vector<std::string> possiblePaths = {
        "../materials/detector-stack.json",      // From build directory
        "materials/detector-stack.json",         // From project root
        "./materials/detector-stack.json",       // Current directory
        "../../materials/detector-stack.json"    // In case of nested build dirs
    };

    for (const auto& path : possiblePaths) {
        jsonFile.open(path);
        if (jsonFile.is_open()) {
            foundPath = path;
            G4cout << "Found JSON file at: " << path << G4endl;
            break;
        }
        jsonFile.clear();
    }

    if (!jsonFile.is_open()) {
        G4Exception("DetectorConstruction::LoadMaterialsFromJSON", "NoJSON", FatalException,
            "Could not find detector-stack.json");
        return;
    }

    std::string line, jsonContent;
    while (std::getline(jsonFile, line)) {
        jsonContent += line + " ";
    }
    jsonFile.close();

    // Parse JSON content manually
    size_t pos = 0;
    fTotalDetectorThickness = 0.0;

    while ((pos = jsonContent.find("\"", pos)) != std::string::npos) {
        pos++;
        size_t nameEnd = jsonContent.find("\"", pos);
        if (nameEnd == std::string::npos) break;

        std::string materialName = jsonContent.substr(pos, nameEnd - pos);
        pos = nameEnd + 1;

        while (pos < jsonContent.length() && (jsonContent[pos] == ' ' || jsonContent[pos] == ':' ||
            jsonContent[pos] == '\n' || jsonContent[pos] == '\t')) pos++;
        if (pos >= jsonContent.length() || jsonContent[pos] != '{') continue;

        int braceCount = 1;
        size_t materialStart = pos + 1;
        pos++;
        while (pos < jsonContent.length() && braceCount > 0) {
            if (jsonContent[pos] == '{') braceCount++;
            else if (jsonContent[pos] == '}') braceCount--;
            pos++;
        }

        std::string materialData = jsonContent.substr(materialStart, pos - materialStart - 1);

        G4double density = 1.0;
        G4double thickness = 1.0;
        std::map<std::string, double> composition;
        G4double r = 0.5, g = 0.5, b = 0.5, a = 0.8;

        // Extract density
        size_t densityPos = materialData.find("\"density\"");
        if (densityPos != std::string::npos) {
            densityPos = materialData.find(":", densityPos) + 1;
            while (densityPos < materialData.length() && (materialData[densityPos] == ' ' ||
                materialData[densityPos] == '\t' || materialData[densityPos] == '\n')) densityPos++;
            size_t densityEnd = materialData.find_first_of(",}", densityPos);
            density = std::stod(materialData.substr(densityPos, densityEnd - densityPos));
        }

        // Extract thickness
        size_t thicknessPos = materialData.find("\"thickness\"");
        if (thicknessPos != std::string::npos) {
            thicknessPos = materialData.find(":", thicknessPos) + 1;
            while (thicknessPos < materialData.length() && (materialData[thicknessPos] == ' ' ||
                materialData[thicknessPos] == '\t' || materialData[thicknessPos] == '\n')) thicknessPos++;
            size_t thicknessEnd = materialData.find_first_of(",}", thicknessPos);
            thickness = std::stod(materialData.substr(thicknessPos, thicknessEnd - thicknessPos));
        }

        // Extract composition
        size_t compStart = materialData.find("\"composition\"");
        if (compStart != std::string::npos) {
            compStart = materialData.find("{", compStart);
            if (compStart != std::string::npos) {
                compStart++;
                size_t compEnd = materialData.find("}", compStart);
                if (compEnd != std::string::npos) {
                    std::string compData = materialData.substr(compStart, compEnd - compStart);

                    size_t elemPos = 0;
                    while (elemPos < compData.length()) {
                        elemPos = compData.find("\"", elemPos);
                        if (elemPos == std::string::npos) break;
                        elemPos++;
                        size_t elemEnd = compData.find("\"", elemPos);
                        if (elemEnd == std::string::npos) break;
                        std::string element = compData.substr(elemPos, elemEnd - elemPos);
                        size_t colonPos = compData.find(":", elemEnd);
                        if (colonPos == std::string::npos) break;
                        elemPos = colonPos + 1;
                        while (elemPos < compData.length() && (compData[elemPos] == ' ' ||
                            compData[elemPos] == '\t' || compData[elemPos] == '\n')) elemPos++;
                        size_t valueEnd = compData.find_first_of(",}", elemPos);
                        if (valueEnd == std::string::npos) valueEnd = compData.length();
                        std::string valueStr = compData.substr(elemPos, valueEnd - elemPos);

                        try {
                            double count = std::stod(valueStr);
                            composition[element] = count;
                        }
                        catch (...) {}

                        elemPos = valueEnd;
                        if (elemPos < compData.length() && compData[elemPos] == ',') elemPos++;
                    }
                }
            }
        }

        // Extract color
        size_t colorStart = materialData.find("\"color\"");
        if (colorStart != std::string::npos) {
            colorStart = materialData.find("{", colorStart) + 1;
            size_t colorEnd = materialData.find("}", colorStart);
            std::string colorData = materialData.substr(colorStart, colorEnd - colorStart);

            auto getColorVal = [&](std::string key) {
                size_t keyPos = colorData.find("\"" + key + "\"");
                if (keyPos != std::string::npos) {
                    keyPos = colorData.find(":", keyPos) + 1;
                    size_t keyEnd = colorData.find_first_of(",}", keyPos);
                    return std::stod(colorData.substr(keyPos, keyEnd - keyPos));
                }
                return 0.5;
                };

            r = getColorVal("r");
            g = getColorVal("g");
            b = getColorVal("b");
            a = getColorVal("a");
        }

        G4Material* material = CreateMaterialFromJSON(G4String(materialName), composition, density * g / cm3);

        MaterialInfo matInfo;
        matInfo.material = material;
        matInfo.logicalVolume = nullptr;
        matInfo.thickness = thickness * mm;
        matInfo.name = G4String(materialName);
        matInfo.color = G4Colour(r, g, b, a);

        fDetectorMaterials.push_back(matInfo);
        fTotalDetectorThickness += matInfo.thickness;
    }
}

G4Material* DetectorConstruction::CreateMaterialFromJSON(const G4String& materialName,
    const std::map<std::string, double>& composition,
    G4double density)
{
    G4NistManager* nist = G4NistManager::Instance();
    G4Material* material = new G4Material(materialName, density, composition.size());

    for (const auto& element : composition) {
        G4Element* el = nist->FindOrBuildElement(element.first);
        if (el) {
            material->AddElement(el, (G4int)element.second);
        }
        else {
            G4cout << "Warning: Element " << element.first << " not found!" << G4endl;
        }
    }

    return material;
}

G4VPhysicalVolume* DetectorConstruction::Construct()
{
    G4bool checkOverlaps = true;

    // Calculate world size based on total detector thickness
    fWorldSizeZ = fTotalDetectorThickness + 4 * mm;

    // World volume
    G4Box* solidWorld = new G4Box("World", fWorldSizeXY / 2, fWorldSizeXY / 2, fWorldSizeZ / 2);
    G4LogicalVolume* logicWorld = new G4LogicalVolume(solidWorld, fWorldMaterial, "World");
    G4VPhysicalVolume* physWorld = new G4PVPlacement(nullptr, G4ThreeVector(),
        logicWorld, "World", nullptr,
        false, 0, checkOverlaps);

    // --- B4C REMOVED ---

    // STARTING POSITION FOR LAYERS
    // We want the stack of layers to be centered in the world.
    // Start at the bottom of the stack: -TotalThickness / 2
    G4double currentZ = -fTotalDetectorThickness / 2.0;

    // Create detector layers from JSON materials
    for (size_t i = 0; i < fDetectorMaterials.size(); ++i) {
        MaterialInfo& matInfo = fDetectorMaterials[i];

        // Move from bottom edge of this layer to its center
        currentZ += matInfo.thickness / 2.0;

        G4Box* solid = new G4Box(matInfo.name, fWorldSizeXY / 2, fWorldSizeXY / 2, matInfo.thickness / 2);
        G4LogicalVolume* logical = new G4LogicalVolume(solid, matInfo.material, matInfo.name);

        new G4PVPlacement(nullptr, G4ThreeVector(0, 0, currentZ), logical,
            matInfo.name, logicWorld, false, 0, checkOverlaps);

        // Set visualization attributes
        G4VisAttributes* visAtt = new G4VisAttributes(matInfo.color);
        visAtt->SetForceSolid(true);
        logical->SetVisAttributes(visAtt);

        // Store logical volume
        matInfo.logicalVolume = logical;

        if (matInfo.name == "GaN") {
            fGaNLogical = logical;
        }

        // Move from center to top edge of this layer (ready for next layer)
        currentZ += matInfo.thickness / 2.0;
    }

    // Make world invisible
    logicWorld->SetVisAttributes(G4VisAttributes::GetInvisible());

    return physWorld;
}

void DetectorConstruction::ConstructSDandField()
{
    G4SDManager* sdManager = G4SDManager::GetSDMpointer();

    // Create sensitive detectors for all imported materials
    for (const auto& matInfo : fDetectorMaterials) {
        G4String sdName = matInfo.name + "_SD";
        SensitiveDetector* sd = new SensitiveDetector(sdName);
        sdManager->AddNewDetector(sd);
        matInfo.logicalVolume->SetSensitiveDetector(sd);
    }
}

G4LogicalVolume* DetectorConstruction::GetMaterialLogical(const G4String& materialName) const
{
    for (const auto& matInfo : fDetectorMaterials) {
        if (matInfo.name == materialName) {
            return matInfo.logicalVolume;
        }
    }
    return nullptr;
}