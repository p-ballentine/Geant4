import uproot
import numpy as np
import matplotlib.pyplot as plt
import json
from mpl_toolkits.mplot3d import Axes3D

def load_detector_geometry(json_path="../materials/detector-stack.json"):
    """Load detector geometry from JSON file"""
    try:
        with open(json_path, 'r') as f:
            materials = json.load(f)
        return materials
    except FileNotFoundError:
        print(f"Warning: Could not find {json_path}, using default geometry")
        return {"GaN": {"density": 6.15, "thickness": 0.5, "composition": {"Ga": 1, "N": 1}}}

def calculate_layer_positions(materials, b4c_thickness=2.6e-3):
    """Calculate z-positions of all detector layers"""
    # B4C is always first (converter layer)
    total_detector_thickness = sum(mat["thickness"] for mat in materials.values())
    total_thickness = b4c_thickness + total_detector_thickness
    
    # B4C layer
    b4c_z_center = -total_thickness/2 + b4c_thickness/2
    layers = {
        "B4C": {
            "z_center": b4c_z_center,
            "thickness": b4c_thickness,
            "z_min": b4c_z_center - b4c_thickness/2,
            "z_max": b4c_z_center + b4c_thickness/2
        }
    }
    
    # JSON materials stacked below B4C
    current_z = b4c_z_center + b4c_thickness/2
    
    for mat_name, mat_info in materials.items():
        thickness = mat_info["thickness"]  # thickness in mm from JSON
        current_z += thickness/2
        
        layers[mat_name] = {
            "z_center": current_z,
            "thickness": thickness,
            "z_min": current_z - thickness/2,
            "z_max": current_z + thickness/2
        }
        
        current_z += thickness/2
    
    return layers

# Load detector configuration
materials_config = load_detector_geometry()
layer_positions = calculate_layer_positions(materials_config)

print("Detector Layer Geometry:")
for layer_name, layer_info in layer_positions.items():
    print(f"{layer_name:8s}: z = [{layer_info['z_min']:8.5f}, {layer_info['z_max']:8.5f}] mm (thickness: {layer_info['thickness']:.5f} mm)")

# Load ROOT data
file = uproot.open("../build/neutron_analysis.root")
step = file["StepData"]

x = step["X"].array(library="np")
y = step["Y"].array(library="np") 
z = step["Z"].array(library="np")
edep = step["EnergyDeposit"].array(library="np")
ptype = step["ParticleName"].array(library="np")
volume = step["VolumeName"].array(library="np")

# Create particle masks
mask_alpha = (ptype == "alpha")
mask_li7 = (ptype == "Li7")
mask_n = (ptype == "neutron")

print(f"\nParticle Statistics:")
print(f"Neutron steps: {np.sum(mask_n)}")
print(f"Alpha steps: {np.sum(mask_alpha)}")  
print(f"Li7 steps: {np.sum(mask_li7)}")

# 3D scatter plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection="3d")

ax.scatter(x[mask_n], y[mask_n], z[mask_n], s=1, c="green", alpha=0.2, label="neutron")
ax.scatter(x[mask_alpha], y[mask_alpha], z[mask_alpha], s=2, c="red", alpha=0.6, label="alpha")
ax.scatter(x[mask_li7], y[mask_li7], z[mask_li7], s=2, c="blue", alpha=0.6, label="Li7")

ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_zlabel("Z (mm)")
ax.legend(loc="upper left")
ax.view_init(elev=-5, azim=45)
plt.tight_layout()
# plt.savefig("plots/spatial-distribution-3d.png")

# Z-distribution with dynamic layer boundaries
fig2, ax2 = plt.subplots(figsize=(10, 6))
bins = np.linspace(z.min(), z.max(), 5000)

ax2.hist(z[mask_n], bins=bins, alpha=0.25, color="green", label="neutron")
ax2.hist(z[mask_alpha], bins=bins, alpha=0.60, color="red", label="alpha")
ax2.hist(z[mask_li7], bins=bins, alpha=0.60, color="blue", label="Li7")

# Draw layer boundaries dynamically
colors = ["red", "green", "blue", "orange", "purple", "brown"]
for i, (layer_name, layer_info) in enumerate(layer_positions.items()):
    color = colors[i % len(colors)]
    ax2.axvline(layer_info["z_min"], color=color, linestyle="--", alpha=0.7, 
                label=f"{layer_name} boundaries")
    ax2.axvline(layer_info["z_max"], color=color, linestyle="--", alpha=0.7)

ax2.set_xlabel("Z position (mm)")
ax2.set_ylabel("Counts / bin")
ax2.legend()
plt.tight_layout()
# plt.savefig("plots/z-distribution.png")

# 2D X–Z projection
fig_xz, ax_xz = plt.subplots(figsize=(8, 6))
ax_xz.scatter(x[mask_n],     z[mask_n],     s=1, c="green", alpha=0.2, label="neutron")
ax_xz.scatter(x[mask_alpha], z[mask_alpha], s=2, c="red",   alpha=0.6, label="alpha")
ax_xz.scatter(x[mask_li7],   z[mask_li7],   s=2, c="blue",  alpha=0.6, label="Li7")
ax_xz.set_xlabel("X (mm)")
ax_xz.set_ylabel("Z (mm)")
ax_xz.legend()
ax_xz.set_title("X–Z Projection")
# Add layer boundaries
for layer_info in layer_positions.values():
    ax_xz.axhline(layer_info["z_min"], color="black", linestyle="--", linewidth=1)
    ax_xz.axhline(layer_info["z_max"], color="black", linestyle="--", linewidth=1)
plt.tight_layout()
plt.savefig("plots/xz-projection.png")


# 2D Y–Z projection
fig_yz, ax_yz = plt.subplots(figsize=(8, 6))
ax_yz.scatter(y[mask_n],     z[mask_n],     s=1, c="green", alpha=0.2, label="neutron")
ax_yz.scatter(y[mask_alpha], z[mask_alpha], s=2, c="red",   alpha=0.6, label="alpha")
ax_yz.scatter(y[mask_li7],   z[mask_li7],   s=2, c="blue",  alpha=0.6, label="Li7")
ax_yz.set_xlabel("Y (mm)")
ax_yz.set_ylabel("Z (mm)")
ax_yz.legend()
ax_yz.set_title("Y–Z Projection")
# Add layer boundaries
for layer_info in layer_positions.values():
    ax_yz.axhline(layer_info["z_min"], color="black", linestyle="--", linewidth=1)
    ax_yz.axhline(layer_info["z_max"], color="black", linestyle="--", linewidth=1)
plt.tight_layout()
plt.savefig("plots/yz-projection.png")

# Print particle distribution by volume
print(f"\nParticle Distribution by Volume:")
for vol_name in np.unique(volume):
    alpha_count = np.sum((ptype == "alpha") & (volume == vol_name))
    li7_count = np.sum((ptype == "Li7") & (volume == vol_name))
    neutron_count = np.sum((ptype == "neutron") & (volume == vol_name))
    print(f"{vol_name:8s}: alpha={alpha_count:6d}, Li7={li7_count:6d}, n={neutron_count:6d}")

plt.show()
