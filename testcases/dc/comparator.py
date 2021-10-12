import re


def extract_device_dimensions(device_path):
    with open(device_path, "r") as f:
        device_model = f.read()

    dimensions = re.findall("Bin[\s0-9,]+(W.*)\n*", device_model)
    dimensions = [x.replace(",", " ") for x in dimensions]
    return dimensions


def generate_xyce_netlist(device_name: str, corner: str, dimensions: str, supply: float):

    file_name = f"{device_name}_{corner}_xyce"

    netlist = f"""*Xyce Common Source Circuit
.lib "../../Models/libs.tech/Xyce/sky130.lib.spice" {corner}

***************
** Parameters
***************
.param width=1
.param length=1

*****************
** main netlist
*****************
X1 d g 0 0 {device_name} {dimension}
R1 d vdd 1000

V1 g 0 1
VDD vdd 0 {supply}

*****************
** Analysic
*****************
.DC v1 0 {supply} 0.1
.print DC FILE=./{file_name}.csv FORMAT=CSV {{-i(vdd)}}

.end
"""
    with open(f"{file_name}.net", "w") as f:
        f.write(netlist)


def generate_ngspice_netlist(device_name: str, corner: str, dimension: str, supply: float):
    width = dimension.split()[2]
    length = dimension.split()[-1]
    file_name = f"{device_name}_{corner}_w_{width}_l_{length}_xyce"

    netlist = f"""*Ngspice Common Source Circuit
.lib "../../Models/libs.tech/Xyce/sky130.lib.spice" {corner}
X1 d g 0 0 {device_name} {dimension}
R1 d vdd 1000

V1 g 0 1
VDD vdd 0 {supply}


.DC v1 0 {supply} 0.1
.print DC FILE=./{file_name}.csv FORMAT=CSV {{-i(vdd)}}

.end
"""

    with open(f"{file_name}.net", "w") as f:
        f.write(netlist)


def simulate(devices_dic):
    corners = ["tt", "ff", "fs", "sf", "ss"]
    for device in devices_dic.keys():
        for corner in corners:
            dimensions = extract_device_dimensions(devices_dic[device]["path"])
            generate_xyce_netlist(
                device_name=device, corner=corner, dimensions=dimensions,
                supply=devices_dic[device]["supply"])

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

    simulate(nmos_devices)


if __name__ == "__main__":
    main()
