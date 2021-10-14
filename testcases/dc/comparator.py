import re
import os
from pathlib import Path
import pandas as pd
import numpy as np


def extract_device_dimensions(device_path):
    """Extract dimensions of bins from device model

    Args:
        device_path (str): path of device model file.gma

    Returns:
        list<str>: List of all device dimensions.
    """
    with open(device_path, "r") as f:
        device_model = f.read()

    dimensions = re.findall("Bin[\s0-9,]+(W.*)\n*", device_model)
    dimensions = [x.replace(",", " ") for x in dimensions]
    return dimensions


def generate_xyce_netlist(device_name: str, corner: str, width: str, length: str, supply: float, file_name: str):
    file_name = file_name + "_xyce"

    netlist = f"""*Xyce Common Source Circuit
.lib "../../Models/libs.tech/Xyce/sky130.lib.spice" {corner}

*****************
** main netlist
*****************
X1 d g 0 0 {device_name} W={width} L={length}
R1 d vdd 1000

V1 g 0 1
VDD vdd 0 {supply}



*****************
** Analysic
*****************
.DC v1 0 {supply} 0.1
.print DC FILE=./xyce_results/{file_name}.csv FORMAT=CSV {{-i(vdd)}}

.end
"""
    with open(f"./xyce_results/{file_name}.net", "w") as f:
        f.write(netlist)


def generate_ngspice_netlist(device_name: str, corner: str, width: str, length: str, supply: float, file_name: str):
    file_name = file_name + "_ngspice"
    netlist = f"""*Ngspice Common Source Circuit
.lib "../../Models/libs.tech/ngspice/sky130.lib.spice" {corner}

*****************
** main netlist
*****************
X1 d g 0 0 {device_name} W={width} L={length}
R1 d vdd 1000

V1 g 0 1
VDD vdd 0 {supply}


*****************
** Analysic
*****************
.control
set appendwrite

shell  rm -rf ./ngspice_results/{file_name}.csv

DC v1 0 {supply} 0.1
wrdata ./ngspice_results/{file_name}.csv  -I(vdd)

.endc
.end
"""
    with open(f"./ngspice_results/{file_name}.net", "w") as f:
        f.write(netlist)


def compare(devices_dic, corners):
    comparison_table = f"Device,Width,Length,Corner,Max_error(%)\n"
    for device in devices_dic.keys():
        for corner in corners:
            dimensions = extract_device_dimensions(devices_dic[device]["path"])
            for dimension in dimensions:
                width = dimension.split()[2]
                length = dimension.split()[-1]
                base_name = f"{device}_W_{width}_L_{length}_{corner}"

                xyce_file_name = f"./xyce_results/{base_name}_xyce.csv"
                ngspice_file_name = f"./ngspice_results/{base_name}_ngspice.csv"

                xyce_df = pd.read_csv(xyce_file_name)
                ngspice_df = pd.read_csv(ngspice_file_name, header=None)

                xyce_result = np.array(list(xyce_df.iloc[:, 0]))
                ngspice_result = np.array(list(ngspice_df.iloc[:, 1]))

                error_percentage = np.abs(
                    (xyce_result-ngspice_result)/xyce_result)*100
                comparison_table += f"{device},{width},{length},{corner},{np.max(error_percentage):.3f}%\n"
                break
            break
        break
    with open("comparison_result.csv", "w")as f:
        f.write(comparison_table)


def simulate(devices_dic, corners):

    for device in devices_dic.keys():
        for corner in corners:
            dimensions = extract_device_dimensions(devices_dic[device]["path"])
            for dimension in dimensions:
                width = dimension.split()[2]
                length = dimension.split()[-1]
                file_name = f"{device}_W_{width}_L_{length}_{corner}"

                Path("./xyce_results").mkdir(parents=True, exist_ok=True)
                Path("./ngspice_results").mkdir(parents=True, exist_ok=True)

                generate_xyce_netlist(device_name=device, corner=corner, width=width, length=length,
                                      supply=devices_dic[device]["supply"], file_name=file_name)

                generate_ngspice_netlist(device_name=device, corner=corner, width=width, length=length,
                                         supply=devices_dic[device]["supply"], file_name=file_name)

                os.system(f"Xyce ./xyce_results/{file_name}_xyce.net")
                os.system(
                    f"ngspice -b ./ngspice_results/{file_name}_ngspice.net")
                os.system(
                    f"sed  -i 's/  /,/g;s/ -/,-/g' ./ngspice_results/{file_name}_ngspice.csv ")
                break
            break
        break


def main():
    nmos_devices = {"sky130_fd_pr__nfet_01v8":     {"supply": 1.8, "path": "../../Models/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__tt.corner.spice"},
                    "sky130_fd_pr__nfet_01v8_lvt": {"supply": 1.8, "path": "../../Models/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8_lvt__tt.corner.spice"},
                    "sky130_fd_pr__nfet_03v3_nvt": {"supply": 3.3, "path": "../../Models/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_03v3_nvt__tt.corner.spice"},
                    "sky130_fd_pr__nfet_05v0_nvt": {"supply": 5.0, "path": "../../Models/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_05v0_nvt__tt.corner.spice"},
                    "sky130_fd_pr__esd_nfet_01v8": {"supply": 1.8, "path": "../../Models/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__esd_nfet_01v8__tt.corner.spice"}, }

    pmos_devices = {"sky130_fd_pr__pfet_01v8":     {"supply": 1.8, "path": "../../Models/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__pfet_01v8__tt.corner.spice"},
                    "sky130_fd_pr__pfet_01v8_lvt": {"supply": 1.8, "path": "../../Models/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__pfet_01v8_lvt__tt.corner.spice"},
                    "sky130_fd_pr__pfet_01v8_hvt": {"supply": 1.8, "path": "../../Models/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__pfet_01v8_hvt__tt.corner.spice"}, }

    corners = ["tt", "ff", "fs", "sf", "ss"]

    simulate(nmos_devices, corners)
    compare(nmos_devices, corners)


if __name__ == "__main__":
    main()
