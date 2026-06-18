#ifndef DETECTORCONSTRUCTION_HH
#define DETECTORCONSTRUCTION_HH

#include "G4VUserDetectorConstruction.hh"

#include "G4Box.hh"
#include "G4Sphere.hh"

#include "G4LogicalVolume.hh"
#include "G4VPhysicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4Material.hh"

#include "G4NistManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"

#include "G4VisAttributes.hh"
#include "G4Color.hh"
#include "G4SDManager.hh"

#include "globals.hh"

#include "SensitiveDetector.hh"

#include "G4ExtendedMaterial.hh"

#include <vector>
#include <map>
#include <string>

struct MaterialInfo {
    G4Material* material;
    G4LogicalVolume* logicalVolume;
    G4double thickness;
    G4double lateralSize;   // square layer side length (x = y)
    G4String name;
    G4Colour color;
};

class DetectorConstruction : public G4VUserDetectorConstruction {
    public:
        DetectorConstruction();
        virtual ~DetectorConstruction();

        virtual G4VPhysicalVolume *Construct() override;
        virtual void ConstructSDandField() override;

        // Getter methods for analysis
        G4LogicalVolume* GetB4CLogical() const { return fB4CLogical; }
        G4LogicalVolume* GetGaNLogical() const { return fGaNLogical; }  // Keep for backward compatibility
        
        // Getter methods for imported materials
        const std::vector<MaterialInfo>& GetDetectorMaterials() const { return fDetectorMaterials; }
        G4LogicalVolume* GetMaterialLogical(const G4String& materialName) const;

    private:
        void DefineMaterials();
        void LoadMaterialsFromJSON();
        G4Material* CreateMaterialFromJSON(const G4String& materialName,
                                         const std::map<std::string, double>& composition,
                                         G4double density);

        // Write the actual constructed geometry (layers, materials, densities,
        // thicknesses, z-extents) to a text file for the analysis/output record.
        void DumpGeometry(const G4String& fileName = "detector_geometry.txt") const;

        // Materials
        G4ExtendedMaterial* fB4CMaterial;
        G4Material* fGaNMaterial;  // Keep for backward compatibility
        G4Material* fWorldMaterial;

        // Logical volumes
        G4LogicalVolume* fB4CLogical;
        G4LogicalVolume* fGaNLogical;  // Keep for backward compatibility

        // Imported material storage
        std::vector<MaterialInfo> fDetectorMaterials;
        G4double fTotalDetectorThickness;

        // Dimensions
        G4double fWorldSizeXY;
        G4double fWorldSizeZ;
        G4double fB4CThickness;
        G4double fGaNThickness;  // Keep for backward compatibility
};

#endif
