import configparser
import os
import json
import shutil

def create_printer_profile(config_file):
    """
    Generates a new printer profile in OrcaSlicer based on a configuration file.

    This script creates the necessary directory structure and JSON files for a new
    printer profile, including machine models, machine variants, filaments, and
    processes. It also copies the required image files.

    Args:
        config_file (str): The path to the configuration file (e.g., 'profile_config.ini').
    """
    config = configparser.ConfigParser()
    config.read(config_file)

    # --- Read Configuration ---
    vendor_name = config.get('vendor', 'name')
    filament_vendor = config.get('vendor', 'filament_vendor')
    printer_models = [model.strip() for model in config.get('printers', 'models').split(',')]
    nozzle_diameters = [diameter.strip() for diameter in config.get('nozzles', 'diameters').split(',')]
    filament_names = [name.strip() for name in config.get('filaments', 'names').split(',')]
    layer_height_percentages = [float(p.strip()) for p in config.get('processes', 'layer_height_percentages').split(',')]
    presets = [p.strip() for p in config.get('processes', 'presets').split(',')]
    gcode_flavor = config.get('gcode', 'flavor')
    bed_model = config.get('images', 'bed_model')
    bed_texture = config.get('images', 'bed_texture')
    printer_cover = config.get('images', 'printer_cover')

    # --- Create Directories ---
    profiles_dir = os.path.join('resources', 'profiles', vendor_name)
    machine_dir = os.path.join(profiles_dir, 'machine')
    process_dir = os.path.join(profiles_dir, 'process')
    filament_dir = os.path.join(profiles_dir, 'filament')

    os.makedirs(machine_dir, exist_ok=True)
    os.makedirs(process_dir, exist_ok=True)
    os.makedirs(filament_dir, exist_ok=True)

    # --- Generate Machine Model and Variant Profiles ---
    for model in printer_models:
        # Create machine model file
        model_data = {
            "type": "machine_model",
            "name": f"{vendor_name} {model}",
            "nozzle_diameter": ";".join(nozzle_diameters),
            "bed_model": f"../../Custom/{bed_model}",
            "bed_texture": f"../../Custom/{bed_texture}",
            "model_id": f"{vendor_name.replace(' ', '_')}_{model}",
            "family": vendor_name,
            "machine_tech": "FFF",
            "default_materials": ";".join([f"{filament_vendor} {name}" for name in filament_names])
        }
        model_filename = os.path.join(machine_dir, f"{vendor_name} {model}.json")
        with open(model_filename, 'w') as f:
            json.dump(model_data, f, indent=4)

        # Create machine variant files
        for nozzle in nozzle_diameters:
            variant_data = {
                "type": "machine",
                "setting_id": f"{vendor_name.replace(' ', '_').upper()}_{model}_{nozzle.replace('.', '')}",
                "name": f"{vendor_name} {model} {nozzle} nozzle",
                "from": "system",
                "instantiation": "true",
                "inherits": "fdm_machine_common",
                "printer_model": f"{vendor_name} {model}",
                "nozzle_diameter": [nozzle],
                "printer_variant": f"{nozzle} nozzle",
                "printable_area": [
                    "0x0",
                    f"{model[3:]}x0",
                    f"{model[3:]}x{model[3:]}",
                    f"0x{model[3:]}"
                ],
                "printable_height": model[3:]
            }
            variant_filename = os.path.join(machine_dir, f"{vendor_name} {model} {nozzle} nozzle.json")
            with open(variant_filename, 'w') as f:
                json.dump(variant_data, f, indent=4)

    # Create fdm_machine_common.json
    shutil.copyfile(os.path.join('resources', 'profiles', 'Custom', 'machine', 'fdm_machine_common.json'),
                    os.path.join(machine_dir, 'fdm_machine_common.json'))

    # --- Generate Filament Profiles ---
    all_variants = [f"{vendor_name} {model} {nozzle} nozzle" for model in printer_models for nozzle in nozzle_diameters]

    for name in filament_names:
        filament_data = {
            "type": "filament",
            "setting_id": f"{filament_vendor.replace(' ', '_').upper()}_{name.replace(' ', '_')}",
            "name": f"{filament_vendor} {name} @{vendor_name}",
            "from": "system",
            "instantiation": "true",
            "inherits": "fdm_filament_common",
            "filament_type": "ABS",
            "filament_vendor": filament_vendor,
            "compatible_printers": all_variants
        }
        filament_filename = os.path.join(filament_dir, f"{filament_vendor} {name} @{vendor_name}.json")
        with open(filament_filename, 'w') as f:
            json.dump(filament_data, f, indent=4)

    fdm_filament_common_data = {
        "type": "filament",
        "name": "fdm_filament_common",
        "from": "system",
        "instantiation": "false",
        "filament_type": "ABS",
        "nozzle_temperature": ["240"],
        "nozzle_temperature_initial_layer": ["240"],
        "hot_plate_temp": ["90"],
        "hot_plate_temp_initial_layer": ["90"],
        "filament_max_volumetric_speed": ["12"]
    }
    fdm_filament_common_filename = os.path.join(filament_dir, 'fdm_filament_common.json')
    with open(fdm_filament_common_filename, 'w') as f:
        json.dump(fdm_filament_common_data, f, indent=4)

    # --- Generate Process Profiles ---
    for model in printer_models:
        for nozzle in nozzle_diameters:
            for i, preset in enumerate(presets):
                layer_height = float(nozzle) * layer_height_percentages[i]
                process_data = {
                    "type": "process",
                    "name": f"{layer_height:.2f}mm {preset} @{vendor_name} {model} {nozzle} nozzle",
                    "from": "system",
                    "instantiation": "true",
                    "inherits": "fdm_process_common",
                    "layer_height": f"{layer_height:.2f}",
                    "compatible_printers": [f"{vendor_name} {model} {nozzle} nozzle"]
                }
                process_filename = os.path.join(process_dir, f"{layer_height:.2f}mm {preset} @{vendor_name} {model} {nozzle} nozzle.json")
                with open(process_filename, 'w') as f:
                    json.dump(process_data, f, indent=4)

    fdm_process_common_data = {
        "type": "process",
        "name": "fdm_process_common",
        "from": "system",
        "instantiation": "false",
        "bottom_shell_layers": "3",
        "top_shell_layers": "3",
        "sparse_infill_density": "15%",
        "wall_loops": "2"
    }
    fdm_process_common_filename = os.path.join(process_dir, 'fdm_process_common.json')
    with open(fdm_process_common_filename, 'w') as f:
        json.dump(fdm_process_common_data, f, indent=4)

    # --- Generate Vendor File ---
    vendor_data = {
        "name": vendor_name,
        "version": "01.00.00.00",
        "force_update": "1",
        "description": f"{vendor_name} printer profiles",
        "machine_model_list": [{
            "name": f"{vendor_name} {model}",
            "sub_path": f"machine/{vendor_name} {model}.json"
        } for model in printer_models],
        "machine_list": [{
            "name": "fdm_machine_common",
            "sub_path": "machine/fdm_machine_common.json"
        }] + [{
            "name": f"{vendor_name} {model} {nozzle} nozzle",
            "sub_path": f"machine/{vendor_name} {model} {nozzle} nozzle.json"
        } for model in printer_models for nozzle in nozzle_diameters],
        "process_list": [{
            "name": "fdm_process_common",
            "sub_path": "process/fdm_process_common.json"
        }] + [{
            "name": f"{float(nozzle) * layer_height_percentages[i]:.2f}mm {preset} @{vendor_name} {model} {nozzle} nozzle",
            "sub_path": f"process/{float(nozzle) * layer_height_percentages[i]:.2f}mm {preset} @{vendor_name} {model} {nozzle} nozzle.json"
        } for model in printer_models for nozzle in nozzle_diameters for i, preset in enumerate(presets)],
        "filament_list": [{
            "name": "fdm_filament_common",
            "sub_path": "filament/fdm_filament_common.json"
        }] + [{
            "name": f"{filament_vendor} {name} @{vendor_name}",
            "sub_path": f"filament/{filament_vendor} {name} @{vendor_name}.json"
        } for name in filament_names]
    }
    vendor_filename = os.path.join('resources', 'profiles', f"{vendor_name}.json")
    with open(vendor_filename, 'w') as f:
        json.dump(vendor_data, f, indent=4)

    # --- Copy Images ---
    for model in printer_models:
        shutil.copyfile(os.path.join('resources', 'profiles', 'Custom', printer_cover),
                        os.path.join(profiles_dir, f"{vendor_name} {model}_cover.png"))

if __name__ == '__main__':
    create_printer_profile('profile_config.ini')
    print("Printer profile created successfully!")
