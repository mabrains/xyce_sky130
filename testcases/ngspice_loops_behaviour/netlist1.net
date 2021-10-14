*Ngspice Common Source Circuit
.lib "../../Models/libs.tech/ngspice/sky130.lib.spice" tt

*****************
** main netlist
*****************
X1 d g 0 0 sky130_fd_pr__nfet_01v8 W=1.68 L=.15
R1 d vdd 1000

V1 g 0 1
VDD vdd 0 1.8


*****************
** Analysic
*****************
.control
set appendwrite
compose width_vector  values 1.26 1.68 1.0 
compose length_vector values 0.15 0.15 1.0 

let i = 0
while i < length(width_vector)
    reset
    alter @m.x1.msky130_fd_pr__nfet_01v8[L] = length_vector[i]
    alter @m.x1.msky130_fd_pr__nfet_01v8[W] = width_vector[i]
    
    DC v1 0 1.8 0.1
    wrdata ./netlist1.csv  -I(vdd)
    
    
    let i = i + 1
end
.endc
.end
