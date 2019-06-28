# -*- coding: utf-8 -*-
"""
Created on Wed Nov 21 13:12:15 2018

@author: kunal
"""
import pickle
import os
import logging
import argparse
import sys
from math import sqrt, ceil
from read_lef import read_lef
from util import convert_to_unit

if not os.path.exists("./LOG"):
    os.mkdir("./LOG")
logging.basicConfig(filename='./LOG/writer.log', level=logging.DEBUG)


class WriteVerilog:
    """ write hierarchical verilog file """

    def __init__(self, circuit_graph, circuit_name, inout_pin_names):
        self.circuit_graph = circuit_graph
        self.circuit_name = circuit_name
        self.inout_pins = inout_pin_names
        self.pins = inout_pin_names

    def print_module(self, fp):
        logging.info("Writing module : %s", self.circuit_name)
        fp.write("\nmodule " + self.circuit_name + " ( ")
        fp.write(', '.join(self.pins))
        fp.write(" ); ")

        if self.inout_pins:
            logging.info("Writing ports : %s", ', '.join(self.inout_pins))
            fp.write("\ninput ")
            fp.write(', '.join(self.inout_pins))
            fp.write(";\n")

        for node, attr in self.circuit_graph.nodes(data=True):
            if 'source' in attr['inst_type']:
                logging.info("Skipping source nodes : %s", node)
                continue
            if 'net' not in attr['inst_type']:
                logging.info("Writing node: %s", node)
                fp.write("\n" + attr['inst_type'] + " " + node + ' ( ')
                ports = []
                nets = []
                if "ports_match" in attr:
                    logging.info("Nets connected to ports: %s",
                                 ', '.join(attr["ports_match"].values()))
                    for key, value in attr["ports_match"].items():
                        ports.append(key)
                        nets.append(value)
                elif "connection" in attr:
                    for key, value in attr["connection"].items():
                        ports.append(key)
                        nets.append(value)                    
                else:
                    logging.info("No connectivity info found : %s",
                                 ', '.join(attr["ports"]))
                    ports = attr["ports"]
                    nets = list(self.circuit_graph.neighbors(node))

                mapped_pins = self.map_pins(ports, nets)
                if mapped_pins:
                    fp.write(', '.join(mapped_pins))
                    fp.write(' ); ')
                else:
                    print("MAPPING NOT CORRECT")

        fp.write("\n\nendmodule\n")

    def map_pins(self, a, b):
        if len(a) == len(b):
            mapped_pins = []
            for i in range(len(a)):
                mapped_pins.append("." + a[i] + "(" + b[i] + ")")

            return mapped_pins
        elif len(set(a)) == len(set(b)):
            if len(a) > len(b):
                mapped_pins = []
                check_sort = []
                no_of_sort = 0
                for i in range(len(a)):
                    if a[i] in check_sort:
                        mapped_pins.append(mapped_pins[check_sort.index(a[i])])
                        no_of_sort += 1
                    else:
                        mapped_pins.append("." + a[i] + "(" +
                                           b[i - no_of_sort] + ")")
                        check_sort.append(a[i])

                return mapped_pins

        else:
            print("unmatched ports found")
            return 0


def print_globals(fp, power):
    """ Write global variables"""
    fp.write("\n\n// End HDL models")
    fp.write("\n// Global nets module")
    fp.write("\n`celldefine")
    fp.write("\nmodule cds_globals;\n")
    for i in range(len(power)):
        fp.write("\nsupply" + str(i) + " " + power[i] + ";")

    fp.write("\n\nendmodule")
    fp.write("\n`endcelldefine")
    fp.close()


def print_header(fp, filename):
    """ Write Verilog header"""
    fp.write("//Verilog block level netlist file for " + filename)
    fp.write("\n//Generated by UMN for ALIGN project \n\n")


def generate_lef(fp, name, values, available_block_lef, 
                 unit_size_mos=10 , unit_size_cap=10):
    """ Creates a shell script to generate parameterized lef"""
    logging.info("checking lef for:%s,%s",name,values)
    #for param, value in size.items():

    if name.lower().startswith('cap'):
        #print("all val",values)
        if 'cap' in values.keys():
            size = '%g'%(round(values["cap"]*1E15,4))
        elif 'c' in values.keys():
            size = '%g'%(round(values["c"]*1E15,4))
        else: 
            convert_to_unit(values)
            size = '_'.join(param+str(values[param]) for param in values)
        logging.info("Found cap with size: %s",size)                
        block_name = name + '_' + size + '_fF'
        unit_block_name = 'cap_' + str(unit_size_cap) + 'f'
        if not block_name in available_block_lef:
            logging.info('Generating lef for: %s %s', name, size)
            fp.write("\npython fabric_" + name + ".py " +
                     " -b " + unit_block_name + 
                     " -n " + str(unit_size_cap))

    elif name.lower().startswith('res'):
        if 'res' in values.keys():
            size = '%g'%(round(values["res"],2))
        elif 'r' in values.keys():
            size = '%g'%(round(values["r"],2))
        else :
            convert_to_unit(values)
            size = '_'.join(param+str(values[param]) for param in values)
        try:
            #size = float(size)
            res_unit_size = 30 * unit_size_cap
            height = ceil(sqrt(float(size) / res_unit_size))
            block_name = name + '_' + size
            if block_name in available_block_lef:
                return block_name
            logging.info('Generating lef for: %s %s', block_name, size)
            fp.write("\npython fabric_" + name + ".py " +
                     " -b " + block_name +
                     " -n " + str(height) +
                     " -r " + size)
        except:
            block_name = name + '_' + size
                

    elif name.lower().startswith('inductor') or \
        name.lower().startswith('spiral'):
        try:
            size = round(values["ind"]*1E12,2)
        except :
            convert_to_unit(values)
            size = '_'.join(param+str(values[param]) for param in values)
            
        ind_unit_size = unit_size_cap
        height = ceil(sqrt(size / ind_unit_size))
        block_name = name + '_' + str(size)
        if block_name in available_block_lef:
            return block_name
        logging.info('Generating lef for: %s %s', block_name, size)
        fp.write("\npython fabric_" + name + ".py " +
                 " -b " + block_name +
                 " -n " + str(height) +
                 " -r " + str(size))
        
    else:
        #print("other param",values)
        if "fin" in values.keys():
            size = int(values["fin"])
            no_units = ceil(size / unit_size_mos)

        elif "l" in values.keys():
            size = int(values["l"]*1E+9)
            no_units = ceil(size / unit_size_mos)

        elif "lr" in values.keys():
            convert_to_unit(values)
            size = '_'.join(param+str(values[param]) for param in values)
            #size = int(values["lr"]*1E+9)
            
        #print(size)
        logging.info('Generating lef for: %s %s', name, str(size))
        if isinstance(size, int):
            no_units = ceil(size / unit_size_mos)
            square_x = ceil(sqrt(no_units))
            while no_units % square_x != 0:
                square_x += 1
            xval = str(square_x)
            yval = str(int(no_units / square_x))
            block_name = (name + "_n" + str(unit_size_mos) +
                        "_X" + xval + "_Y" + yval)
            if block_name in available_block_lef:
                return block_name
            logging.info("Generating parametric lef of: %s", block_name)
            fp.write("\npython fabric_" + name + ".py " +
                     " -b " + block_name +
                     " -n " + str(unit_size_mos) +
                     " -X " + xval +
                     " -Y " + yval )
        else:
            logging.info("No proper marameters found for cell generation")
            block_name = name+"_"+size       

    return block_name


#%%
if __name__ == '__main__':
    if not os.path.exists("./results/"):
        os.mkdir("./results/")
    RESULT_DIR = "./results/"
    logging.info("Writing results in ./results dir: ")

    PARSER = argparse.ArgumentParser(
        description="directory path for input circuits")
    PARSER.add_argument("-U_mos",
                        "--unit_size_mos",
                        type=int,
                        default=10,
                        help='no of fins in unit size')
    PARSER.add_argument("-U_cap",
                        "--unit_size_cap",
                        type=int,
                        default=10,
                        help='no of fins in unit size')
    ARGS = PARSER.parse_args()

    FILE_NAMES = os.listdir(RESULT_DIR)
    INPUT_PICKLE = []
    for files in FILE_NAMES:
        if files.endswith('.p'):
            INPUT_PICKLE.append(files[:-2])
            logging.info("Searching file: %s", files)
    logging.info("Found files: %s", ", ".join(INPUT_PICKLE))
    try:
        INPUT_PICKLE = INPUT_PICKLE[0]
    except ValueError:
        print("ERROR: No input file. Exiting verilog writer")
        sys.exit()
    logging.info("Picking first file for generating results: %s", INPUT_PICKLE)
    # write a verilog file
    VERILOG_FP = open(RESULT_DIR + INPUT_PICKLE + '.v', 'w')
    LEF_FP = open(RESULT_DIR + INPUT_PICKLE + '_lef.sh', 'w')
    LEF_FP.write('# file to generate lef')
    print_header(VERILOG_FP, INPUT_PICKLE)
    POWER_PINS = ["vdd!", "gnd"]
    #read lef to not write those modules as macros
    ALL_LEF = read_lef()
    logging.info("Reading available lef: %s", ", ".join(ALL_LEF))

    UNIT_SIZE_CAP = ARGS.unit_size_cap
    UNIT_SIZE_MOS = ARGS.unit_size_cap
    logging.info("Unit cap cell size: %s", str(UNIT_SIZE_CAP))
    logging.info("Unit mos cell size: %s", str(UNIT_SIZE_MOS))
    logging.info("Reading file: %s", RESULT_DIR + INPUT_PICKLE + '.p')

    with open(RESULT_DIR + INPUT_PICKLE + '.p', 'rb') as fp:
        list_graph = pickle.load(fp)
    #print(list_graph)
    generated_module=[]
    for members in list_graph:
        #print(members)
        name = members["name"]
        logging.info("Found module: %s", name)
        if 'ports_match' in members.keys():
            logging.info("Ports in module: %s",
                         ", ".join(members['ports_match']))

        graph = members["lib_graph"].copy()
        logging.info("Reading nodes from graph: %s", str(graph))
        for node, attr in graph.nodes(data=True):
            #lef_name = '_'.join(attr['inst_type'].split('_')[0:-1])
            if 'net' in attr['inst_type']: continue
            lef_name = attr['inst_type']
            if "values" in attr and (lef_name in ALL_LEF):
                block_name = generate_lef(LEF_FP, lef_name, attr["values"],
                                         ALL_LEF, UNIT_SIZE_MOS, UNIT_SIZE_CAP)
                logging.info("Created new lef for: %s", block_name)
                ALL_LEF.append(block_name)
                graph.nodes[node]['inst_type'] = block_name
            else:
                logging.info("WARNING:No physical information found for: %s",
                             name)

        if name in ALL_LEF or name in generated_module[:-1]:
            continue
        if "ports" in members.keys():
            inoutpin = members["ports"]
        elif "ports_match" in members.keys():
            inoutpin = members["ports_match"]
        else:
            inoutpin = []
        #print("inout pins:",inoutpin)
        logging.info("writing verilog for block: %s", name)
        wv = WriteVerilog(graph, name, inoutpin)
        wv.print_module(VERILOG_FP)
        generated_module.append(name)

    LEF_FP.close()

    print("OUTPUT LEF generator:", RESULT_DIR + INPUT_PICKLE + "_lef.sh")
    #print_globals(VERILOG_FP, POWER_PINS)
    print("OUTPUT verilog netlist at:", RESULT_DIR + INPUT_PICKLE + ".v")
