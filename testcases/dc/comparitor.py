

def generate_xyce_netlist(device_name, device_path):
    netlist = f"""
*Xyce Common Source Circuit
.lib "../../Models/libs.tech/Xyce/sky130.lib.spice" tt
X1 d g 0 0 {device_name} L=1 W=2 
R1 d vdd 1000

V1 g 0 1
VDD vdd 0 1.8


.DC v1 0 1.8 0.1
.print DC {{-i(vdd)}}

.end

    
"""


def main():
    nmos_devices = {"sky130_fd_pr__nfet_01v8":     {"supply": 1.8, "path": "../../libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__tt.corner.spice"},
                    "sky130_fd_pr__nfet_01v8_lvt": {"supply": 1.8, "path": "../../libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8_lvt__tt.corner.spice"},
                    "sky130_fd_pr__nfet_03v3_nvt": {"supply": 3.3, "path": "../../libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_03v3_nvt__tt.corner.spice"},
                    "sky130_fd_pr__nfet_05v0_nvt": {"supply": 5.0, "path": "../../libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_05v0_nvt__tt.corner.spice"},
                    "sky130_fd_pr__esd_nfet_01v8": {"supply": 1.8, "path": "../../libs.ref/sky130_fd_pr/spice/sky130_fd_pr__esd_nfet_01v8__tt.corner.spice"}, }

    pmos_devices = {"sky130_fd_pr__pfet_01v8":     {"supply": 1.8, "path": "../../libs.ref/sky130_fd_pr/spice/sky130_fd_pr__pfet_01v8__tt.corner.spice"},
                    "sky130_fd_pr__pfet_01v8_lvt": {"supply": 1.8, "path": "../../libs.ref/sky130_fd_pr/spice/sky130_fd_pr__pfet_01v8_lvt__tt.corner.spice"},
                    "sky130_fd_pr__pfet_01v8_hvt": {"supply": 1.8, "path": "../../libs.ref/sky130_fd_pr/spice/sky130_fd_pr__pfet_01v8_hvt__tt.corner.spice"}, }


if __name__ == "__main__":
    main()
