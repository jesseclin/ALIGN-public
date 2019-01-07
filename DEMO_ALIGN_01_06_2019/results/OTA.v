//Verilog block level netlist file for OTA
//Generated by UMN for ALIGN project 


module DC_converter_2018_11_09_ASAP7_current_mirror_ota_schematic ( vg, net08, net09, voutn, voutp, id ); 
inout vg, net08, net09, voutn, voutp, id;

Switch_NMOS_10_1x1 m11 ( .S(net3), .D(net1), .G(net2) ); 

endmodule

module top (  ); 
DP_NMOS_75_3x10 m1_m0 ( .S(net10), .D2(net8), .G2(vinp), .G1(vinn), .D1(net014) ); 
DC_converter_2018_11_09_ASAP7_current_mirror_ota_schematic i0 ( .vg(vg), .net08(net08), .net09(net09), .voutn(voutn), .voutp(voutp), .id(id) ); 
SCM_NMOS_50_1x12 m3_m4 ( .S(0), .D2(net10), .D1(id) ); 
CMC_PMOS_15_1x6 m6_m7 ( .S2(net06), .S1(net012), .D2(voutn), .G(vbiasp), .D1(voutp) ); 
CMC_NMOS_25_1x10 m10_m2 ( .S2(net8), .S1(net014), .D2(voutn), .G(vbiasn), .D1(voutp) ); 
CMC_PMOS_10_1x4 m9_m8 ( .S(vdd!), .D2(net06), .G(vbiasp1), .D1(net012) ); 

endmodule


// End HDL models
// Global nets module
`celldefine
module cds_globals;

supply0 VDD;
supply1 VSS;

endmodule
`endcelldefine