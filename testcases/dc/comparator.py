import re
import os
from pathlib import Path
import pandas as pd


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


def generate_xyce_netlist(device_name: str, corner: str, dimensions: str, supply: float, file_name: str):
    file_name = file_name + "_xyce"
    dimensions_data = [
        f"+ {dimension.split()[2]} {dimension.split()[-1]}" for dimension in dimensions]
    dimensions_data = "\n".join(dimensions_data)

    netlist = f"""*Xyce Common Source Circuit
.lib "../../Models/libs.tech/Xyce/sky130.lib.spice" {corner}

***************
** Parameters
***************
.param width=1.68
.param length=0.15

*****************
** main netlist
*****************
X1 d g 0 0 {device_name} W=width L=length
R1 d vdd 1000

V1 g 0 1
VDD vdd 0 {supply}

********
** data
********
.data device_data
+ width length
{dimensions_data}
.enddata

*****************
** Analysic
*****************
.DC v1 0 {supply} 0.1
.STEP DATA=device_data
.print DC FILE=./xyce_results/{file_name}.csv FORMAT=CSV {{-i(vdd)}}

.end
"""
    with open(f"./xyce_results/{file_name}.net", "w") as f:
        f.write(netlist)


def generate_ngspice_netlist(device_name: str, corner: str, dimensions: str, supply: float, file_name: str):
    file_name = file_name + "_ngspice"
    width_data = [dimension.split()[2] for dimension in dimensions]
    width_data = " ".join(width_data)

    length_data = [dimension.split()[-1] for dimension in dimensions]
    length_data = " ".join(length_data)

    netlist = f"""*Ngspice Common Source Circuit
.lib "../../Models/libs.tech/ngspice/sky130.lib.spice" {corner}

*****************
** main netlist
*****************
X1 d g 0 0 {device_name} W=1.68 L=.15
R1 d vdd 1000

V1 g 0 1
VDD vdd 0 {supply}


*****************
** Analysic
*****************
.control
set appendwrite
compose width_vector  values {width_data}
compose length_vector values {length_data}

shell  rm -rf ./ngspice_results/{file_name}.csv

let i = 0
while i < length(width_vector)
    reset
    alter @m.x1.m{device_name}[L] = length_vector[i]
    alter @m.x1.m{device_name}[W] = width_vector[i]
    
    DC v1 0 {supply} 0.1
    wrdata ./ngspice_results/{file_name}.csv  -I(vdd)
    
    
    let i = i + 1
end
.endc
.end
"""
    with open(f"./ngspice_results/{file_name}.net", "w") as f:
        f.write(netlist)


def compare(devices_dic, corners):
    for device in devices_dic.keys():
        for corner in corners:
            base_name = f"{device}_{corner}"
            xyce_file_name = f"./xyce_results/{base_name}_xyce.csv"
            ngspice_file_name = f"./ngspice_results/{base_name}_ngspice.csv"

            xyce_df = pd.read_csv(xyce_file_name)
            ngspice_df = pd.read_csv(ngspice_file_name)

            print(xyce_df[0][0])

            break
        break


def simulate(devices_dic, corners):

    for device in devices_dic.keys():
        for corner in corners:
            file_name = f"{device}_{corner}"
            dimensions = extract_device_dimensions(devices_dic[device]["path"])

            Path("./xyce_results").mkdir(parents=True, exist_ok=True)
            Path("./ngspice_results").mkdir(parents=True, exist_ok=True)

            generate_xyce_netlist(device_name=device, corner=corner, dimensions=dimensions,
                                  supply=devices_dic[device]["supply"], file_name=file_name)

            generate_ngspice_netlist(device_name=device, corner=corner, dimensions=dimensions,
                                     supply=devices_dic[device]["supply"], file_name=file_name)

            # os.system(f"Xyce ./xyce_results/{file_name}_xyce.net")
            # os.system(f"ngspice -b ./ngspice_results/{file_name}_ngspice.net")
            # os.system(
            #     f"sed  -i 's/  /,/g;s/ -/,-/g' ./ngspice_results/{file_name}_ngspice.csv ")

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
