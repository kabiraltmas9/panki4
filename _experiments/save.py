import os
import yaml

# Prompt the user for the experiment number
experiment_number = int(input("Enter the experiment number: "))

# File paths
crazyflies_config_path = "../crazyflie/config/crazyflies.yaml"
info_file_path = f"info/info{experiment_number}.yaml"

# file guard
if os.path.exists(info_file_path):
    print(f"File already exists: {info_file_path}")
    ans = input("Overwrite? [y/n]: ")
    if ans == "n":
        print("Exiting...")
        exit(1)

# Dictionary to store extracted information
info = {}
info["experiment_number"] = experiment_number

# Read information from crazyflies.yaml
try:
    with open(crazyflies_config_path, "r") as config_file:
        config_data = yaml.safe_load(config_file)
        # extract the trajectory and timescale
        obj = config_data["all"]["firmware_params"]
        if "ctrlLeeInfo" in obj:
            for key, value in obj["ctrlLeeInfo"].items():
                info[key] = value
        # extract the ctrlLee parameters
        if "ctrlLee" in obj:
            for key, value in obj["ctrlLee"].items():
                info[key] = value
except FileNotFoundError:
    print(f"File not found: {crazyflies_config_path}")
    exit(1)

# Write the experiment info to the info file
custom_key_order = ["trajectory",
                    "timescale",
                    "motors",
                    "propellers",
                    "Kpos_Px",
                    "Kpos_Py",
                    "Kpos_Pz",
                    "Kpos_Ix",
                    "Kpos_Iy",
                    "Kpos_Iz",
                    "Kpos_Dx",
                    "Kpos_Dy",
                    "Kpos_Dz",
                    "KR_x",
                    "KR_y",
                    "KR_z",
                    "KI_x",
                    "KI_y",
                    "KI_z",
                    "Kw_x",
                    "Kw_y",
                    "Kw_z",
                    "mass"]

try:
    with open(info_file_path, "w") as info_file:
        for key in custom_key_order:
            if key in info:
                yaml.dump({key: info[key]}, info_file, default_flow_style=False, sort_keys=False)
    print(f"Experiment info written to {info_file_path}")
except Exception as e:
    print(f"Error writing to {info_file_path}: {str(e)}")