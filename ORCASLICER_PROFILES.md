# OrcaSlicer Profile System Architecture

## Overview
OrcaSlicer uses a JSON-based profile system that supports inheritance, allowing for a modular and extensible configuration for printers, filaments, and print processes. Profiles are categorized into three main types: **Machine** (Printer), **Filament**, and **Process**.

## 1. File Structure & Location

### Repository Location
Profiles are stored in the `resources/profiles` directory within the OrcaSlicer repository.
-   **Vendor Folders**: Each printer manufacturer has its own folder (e.g., `resources/profiles/BBL`, `resources/profiles/Creality`).
-   **Filament Library**: A global library exists at `resources/profiles/OrcaFilamentLibrary`.

### Directory Layout (Vendor Folder)
```
resources/profiles/VendorName/
├── VendorName.json          # Vendor Meta File (Manifest)
├── machine/                 # Printer definitions
│   ├── ModelName.json       # Machine Model (Base)
│   └── VariantName.json     # Machine Variant (Specific Nozzle/Config)
├── filament/                # Vendor-specific filaments
│   └── FilamentName.json
├── process/                 # Print process settings
│   └── ProcessName.json
└── [ModelName]_cover.png    # Thumbnail image for the printer
```

### User Storage Location (Windows)
User-created and modified profiles are stored in the AppData directory:
-   `%APPDATA%\OrcaSlicer\user\[UserID]\`
-   System profiles are cached in `%APPDATA%\OrcaSlicer\system\`

## 2. Profile Types & JSON Format

### Common Fields
All profile JSON files share some common fields:
-   `type`: `machine`, `machine_model`, `filament`, or `process`.
-   `name`: Unique name of the profile.
-   `from`: Origin of the profile (e.g., `system`, `user`).
-   `inherits`: Name of the parent profile to inherit settings from.
-   `instantiation`: `true` if this is a usable profile, `false` if it's an abstract base.

### Machine Model (`machine_model`)
Defines the physical printer hardware base.
-   **Key Fields**: `nozzle_diameter`, `bed_model` (STL), `bed_texture` (SVG/PNG), `model_id`.
-   **Example**: `Orca 3D Fuse1.json`

### Machine Variant (`machine`)
Defines a specific configuration of a printer model (e.g., specific nozzle size).
-   **Inheritance**: Inherits from a common base (e.g., `fdm_machine_common`).
-   **Key Fields**: `printer_model`, `nozzle_diameter`, `printable_area`.
-   **Example**: `Orca 3D Fuse1 0.4 nozzle.json`

### Filament (`filament`)
Defines material properties.
-   **Inheritance**: Can inherit from `OrcaFilamentLibrary` profiles (e.g., `Generic PLA @System`).
-   **Key Fields**: `filament_type`, `filament_flow_ratio`, `compatible_printers`.
-   **Example**: `Generic PLA @Orca 3D Fuse1.json`

### Process (`process`)
Defines print settings (layer height, speed, infill).
-   **Inheritance**: Inherits from `fdm_process_common`.
-   **Key Fields**: `layer_height`, `compatible_printers`.
-   **Example**: `0.20mm Standard @Orca 3D Fuse1 0.4.json`

## 3. Inheritance Mechanism
OrcaSlicer uses a hierarchical inheritance model.
1.  **Base Profile**: Defines default values for all settings (e.g., `fdm_machine_common.json`).
2.  **Derived Profile**: Specifies `inherits: "BaseProfileName"`.
3.  **Override**: The derived profile only needs to list keys that differ from the base.
4.  **Runtime Composition**: When loaded, the system applies the base settings first, then overwrites them with the derived profile's values.

## 4. Naming Conventions

-   **Vendor Profile**: `VendorName.json`
-   **Printer Model**: `VendorName ModelName.json`
-   **Printer Variant**: `VendorName ModelName NozzleSize nozzle.json`
-   **Filament**: `Brand Type @Vendor Model.json` (e.g., `Generic PLA @Creality Ender3`)
-   **Process**: `LayerHeight ProfileType @Vendor Model.json` (e.g., `0.20mm Standard @Creality Ender3`)

## 5. UI Assets

### Printer Thumbnails
-   **Format**: PNG
-   **Resolution**: Typically 240x240px (or similar square aspect ratio).
-   **Location**: Inside the vendor folder (`resources/profiles/VendorName/`).
-   **Naming**: `[machine_model_list.name]_cover.png`.
    -   *Example*: If `machine_model_list` has name "Bambu Lab X1 Carbon", the image must be `Bambu Lab X1 Carbon_cover.png`.

### Bed Textures
-   **Format**: SVG or PNG.
-   **Location**: Referenced in `machine_model` JSON under `bed_texture`.
-   **Path**: Relative to the profile or in a common resource path.

## 6. Codebase Reference

### Key Files
-   **`src/libslic3r/Preset.cpp`**: Core logic for loading, saving, and managing presets. Handles inheritance and validation.
-   **`src/libslic3r/PrintConfig.cpp`**: Defines all configuration keys, their types, and default values.
-   **`src/libslic3r/PresetBundle.cpp`**: Manages collections of presets (Machine, Filament, Process) and their inter-dependencies.
-   **`src/libslic3r/Utils.cpp`**: Contains utility functions, including data directory resolution (`data_dir()`).

### Ingestion Logic
1.  **Boot**: `OrcaSlicer` initializes `PresetBundle`.
2.  **Load**: Scans `resources/profiles` and `%APPDATA%/OrcaSlicer`.
3.  **Parse**: Uses `boost::property_tree` or `nlohmann::json` to parse JSON files.
4.  **Resolve**: Resolves `inherits` links to build the full configuration object (`FullPrintConfig`).

### Saving Logic
1.  **Diff**: When saving a user preset, it calculates the diff against the parent system preset.
2.  **Write**: Saves only the changed keys to a new JSON file in the User AppData folder.
