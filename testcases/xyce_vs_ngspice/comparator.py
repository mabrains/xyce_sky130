"""comparator
Usage:
  comparator.py --analysis=<analysis> [--num_cores=<num>] options

Options:
  -h, --help             Show help text.
  -v, --version          Show version.
  --num_cores=<num>      Number of cores to be used by simulator
  --analysis=<analysis>  Required analysis to run valid options are {DC,AC,Transient, OP}
"""

import re
import os
from pathlib import Path
import pandas as pd
import numpy as np
import concurrent.futures
from docopt import docopt


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


def generate_xyce_netlist(device_name: str, corner: str, width: str, length: str, supply: float, file_name: str, analysis: str):
    """Generate xyce netlist for given analysis

    Args:
        device_name (str): Name of device to simulate.
        corner (str): Name of corner to run.
        width (str): Width of transistor.
        length (str): Length of transistor.
        supply (float): Supply voltage.
        file_name (str): Netlist file name.
        analysis (str): Type of analysis to perform
    """
    file_name = file_name + "_xyce"

    if analysis.lower() == "dc":
        analysis_line = f".DC v1 0 {supply} 0.1"
        print_line = f".print DC FILE=./xyce_results/{file_name}.csv FORMAT=CSV {{-i(vdd)}}"
    elif analysis.lower() == "ac":
        analysis_line = f".AC DEC 10 1 1000G"
        print_line = f".print AC FILE=./xyce_results/{file_name}.csv FORMAT=CSV {{vdb(d)}}"
    elif analysis.lower() == "transient":
        pass
    elif analysis.lower() == "op":
        analysis_line = f".op"
        print_line = f".print DC FILE=./xyce_results/{file_name}.csv FORMAT=CSV {{v(d)}}"

    netlist = f"""* Xyce Common Source Circuit

.lib "../../Models/libs.tech/Xyce/sky130.lib.spice" {corner}

*****************
** main netlist
*****************
X1 d g 0 0 {device_name} W = {width} L = {length}
R1 d vdd 1000

V1 g 0 DC 1 AC 1 SIN(0 1 1k)
VDD vdd 0 {supply}


*****************
** Analysic
*****************
{analysis_line}
{print_line}

.end
"""

    with open(f"./xyce_results/{file_name}.net", "w") as f:
        f.write(netlist)


def generate_ngspice_netlist(device_name: str, corner: str, width: str, length: str, supply: float, file_name: str, analysis: str):
    """Generate Ngspice netlist for given analysis

    Args:
        device_name (str): Name of device to simulate.
        corner (str): Name of corner to run.
        width (str): Width of transistor.
        length (str): Length of transistor.
        supply (float): Supply voltage.
        file_name (str): Netlist file name.
        analysis (str): Type of analysis to perform
    """

    file_name = file_name + "_ngspice"
    if analysis.lower() == "dc":
        analysis_line = f"DC v1 0 {supply} 0.1"
        print_line = f"wrdata ./ngspice_results/{file_name}.csv  -I(vdd)"
    elif analysis.lower() == "ac":
        analysis_line = f"AC DEC 10 1 1000G"
        print_line = f"wrdata ./ngspice_results/{file_name}.csv  vdb(d)"
    elif analysis.lower() == "transient":
        pass
    elif analysis.lower() == "op":
        analysis_line = f"OP"
        print_line = f"wrdata ./ngspice_results/{file_name}.csv  {{v(d)}}"

    netlist = f"""*Ngspice Common Source Circuit
.lib "../../Models/libs.tech/ngspice/sky130.lib.spice" {corner}

*****************
** main netlist
*****************
X1 d g 0 0 {device_name} W={width} L={length}
R1 d vdd 1000

V1 g 0 DC 1 AC 1 SIN(0 1 1k)
VDD vdd 0 {supply}


*****************
** Analysic
*****************
.control
set appendwrite

shell  rm -rf ./ngspice_results/{file_name}.csv

{analysis_line}
{print_line}

.endc
.end
"""
    with open(f"./ngspice_results/{file_name}.net", "w") as f:
        f.write(netlist)


def compare(devices_dic, corners, analysis):
    """Compare Xyce and Ngspice run result

    Args:
        devices_dic (dic): Dictionary containing all devices to test.
        corners (List<str>): List contains all corners.
        analysis (str): Name of analysis to compare.
    """
    comparison_table = f"Device,Width,Length,Corner,Max_error(%)\n"
    for device in devices_dic.keys():
        for corner in corners:
            dimensions = extract_device_dimensions(devices_dic[device]["path"])
            for dimension in dimensions:
                width = dimension.split()[2]
                length = dimension.split()[-1]
                base_name = f"{device}_{analysis}_W_{width}_L_{length}_{corner}"

                xyce_file_name = f"./xyce_results/{base_name}_xyce.csv"
                ngspice_file_name = f"./ngspice_results/{base_name}_ngspice.csv"

                xyce_df = pd.read_csv(xyce_file_name)
                ngspice_df = pd.read_csv(ngspice_file_name, header=None)

                if analysis.lower() == "ac":
                    xyce_result = np.array(list(xyce_df.iloc[:, 1]))
                else:
                    xyce_result = np.array(list(xyce_df.iloc[:, 0]))

                ngspice_result = np.array(list(ngspice_df.iloc[:, 1]))

                filter_xyce = np.abs(xyce_result) > 1e-9
                filter_ngspice = np.abs(ngspice_result) > 1e-9
                xyce_result = xyce_result[filter_xyce]
                ngspice_result = ngspice_result[filter_ngspice]

                error_percentage = np.abs(
                    (xyce_result-ngspice_result)/xyce_result)*100
                comparison_table += f"{device},{width},{length},{corner},{np.max(error_percentage):.3f}%\n"

            break
        break
    with open(f"comparison_result_{analysis}.csv", "w")as f:
        f.write(comparison_table)


def call_simulator(file_name):
    """Call simulation commands to perform simulation.

    Args:
        file_name (str): Netlist file name.
    """
    os.system(f"Xyce ./xyce_results/{file_name}_xyce.net")
    os.system(
        f"ngspice -b ./ngspice_results/{file_name}_ngspice.net")
    os.system(
        f"sed  -i 's/  /,/g;s/ -/,-/g' ./ngspice_results/{file_name}_ngspice.csv ")


def simulate(devices_dic, corners, num_cores, analysis):
    """Simulate xyce and ngspice generated netlists.

    Args:
        devices_dic (dic): Dictionary containing all devices to simulate.
        corners (List<str>):  List contains all corners.
        num_cores (int): Num of cores to run on.
        analysis (str): Type of analysis to perform.
    """
    workers_count = num_cores
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers_count) as executor:

        for device in devices_dic.keys():
            for corner in corners:
                dimensions = extract_device_dimensions(
                    devices_dic[device]["path"])
                for dimension in dimensions:
                    width = dimension.split()[2]
                    length = dimension.split()[-1]
                    file_name = f"{device}_{analysis}_W_{width}_L_{length}_{corner}"

                    Path("./xyce_results").mkdir(parents=True, exist_ok=True)
                    Path("./ngspice_results").mkdir(parents=True, exist_ok=True)

                    generate_xyce_netlist(device_name=device, corner=corner, width=width, length=length,
                                          supply=devices_dic[device]["supply"], file_name=file_name, analysis=analysis)

                    generate_ngspice_netlist(device_name=device, corner=corner, width=width, length=length,
                                             supply=devices_dic[device]["supply"], file_name=file_name, analysis=analysis)

                    executor.submit(call_simulator, file_name)

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

    arguments = docopt(__doc__, version='comparator: 0.1')

    if arguments["--analysis"].lower() not in ["dc", "ac", "transient", "op"]:
        print(
            "ERROR: --analysis should be one of {'DC', 'AC', 'Transient, 'OP'}")
        exit()

    if arguments["--analysis"].lower() == "transient":
        print("Transient comparison is not supported yet.")
        exit()

    num_cores = 1 if arguments["--num_cores"] == None else int(
        arguments["--num_cores"])

    simulate(nmos_devices, corners, num_cores, arguments["--analysis"])
    compare(nmos_devices, corners, arguments["--analysis"])


if __name__ == "__main__":
    main()
