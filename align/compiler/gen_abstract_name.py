# -*- coding: utf-8 -*-
"""
Created on Wed Feb 2 13:12:15 2022

@author: kunal
"""
from align.schema.types import set_context
import logging
import hashlib
import pathlib


from align.schema import SubCircuit, Model, constraint, Library, Instance
from align.primitive.main import get_generator

logger = logging.getLogger(__name__)

class PrimitiveLibrary():

    def __init__(self, ckt_lib:Library, pdk_dir: pathlib.Path):
        pdk_models = get_generator('pdk_models', pdk_dir)
        self.pdk_dir = pdk_dir
        self.plib = Library(loadbuiltins=True, pdk_models=pdk_models)
        self.ckt_lib = ckt_lib

    def gen_primitive_collateral(self):
        """
        create a unique name for each instance and
        Args:
            ckt_data ([type]): ckt library after annotation
        Returns:
            primitives: library of primitives
        """

        for ckt in self.ckt_lib:
            if not isinstance(ckt, SubCircuit):
                continue
            elif [True for const in ckt.constraints if isinstance(const, constraint.Generator)]:
                continue
            logger.debug(f"Found module: {ckt.name} {ckt.elements} {ckt.pins}")
            group_cap_instances = []
            for const in ckt.constraints:
                if isinstance(const, constraint.GroupCaps):
                    group_cap_instances.append(const.name.upper())
                    self.group_cap_subcircuit(const.unit_cap.upper())
            logger.info(f"found group cap instances {group_cap_instances}")

            for ele in ckt.elements:
                if ele.name in group_cap_instances:
                    ele.add_abs_name(ele.model)

                    logger.info(f"group cap instance {ele}")
                else:
                    self.gen_primitive_def(ele)
        return self.plib

    def _gen_key(self, param):
        """_gen_key
        Creates a hex key for combined transistor params
        Args:
            param (dict): dictionary of parameters
        Returns:
            str: unique hex key
        """
        skeys = sorted(param.keys())
        arg_str = '_'.join([k+':'+str(param[k]) for k in skeys])
        key = f"_{str(int(hashlib.sha256(arg_str.encode('utf-8')).hexdigest(), 16) % 10**8)}"
        return key

    def group_cap_subcircuit(self, unit_cap):
        #TODO hack for group cap, need to be fixed
        """create subckt corresponding to unit cap
        Args:
            name (str): unique cap name in constraint
        """
        if not self.plib.find(unit_cap):
            logger.debug(f"creating subcircuit for {unit_cap}")
            cmodel = self.plib.find('CAP')
            assert cmodel, f"no cap model found for groupcap constraint {cmodel}"
            unit_cap_value = float(unit_cap.split('_')[1].replace('F', ''))*10E-15

            with set_context(self.plib):
                new_subckt = SubCircuit(name=unit_cap, pins=list(cmodel.pins), generator={"name": 'CAP'})
            with set_context(new_subckt.elements):
                new_ele = Instance(name='C0', model='CAP',
                                   pins={pin: pin for pin in cmodel.pins},
                                   parameters={'VALUE': unit_cap_value}
                                   )
                new_subckt.elements.append(new_ele)
            self.plib.append(new_subckt)

    def create_subckt(self, element, name):
        """create_subckt
        Adds a subckt in primitive library for a generic device instance if not already existing
        Args:
            element (instance): instance in a subcircuit
            name (str): unique name for this instance based on parameters
        """
        if not self.plib.find(name):
            logger.debug(f"creating subcircuit for {element}")
            with set_context(self.plib):
                new_subckt = SubCircuit(name=name, pins=list(element.pins.keys()), generator={"name":element.model})
            with set_context(new_subckt.elements):
                new_ele = Instance(name=element.name,
                                   model=element.model,
                                   pins={x: x for x in element.pins.keys()},
                                   parameters=element.parameters
                                   )
                new_subckt.elements.append(new_ele)
            self.plib.append(new_subckt)

    def gen_primitive_def(self, element):
        """gen_primitive_def

            Adds subcircuits to primitive library for each instance with a different parameter

        Args:
            element (instance): instance properties
        """
        model = element.model
        generator = self.ckt_lib.find(model)

        if isinstance(generator, SubCircuit):
            element.add_abs_name(model)
            gen_const = [True for const in generator.constraints if isinstance(const, constraint.Generator)]
            if gen_const and not self.plib.find(generator.name):
                with set_context(self.plib):
                    self.plib.append(generator)
        elif get_generator(element.model, self.pdk_dir):
            block_arg = self._gen_key(element.parameters)
            unique_name = f'{model}{block_arg}'
            element.add_abs_name(unique_name)
            if not self.plib.find(model):
                with set_context(self.plib):
                    self.plib.append(self.ckt_lib.find(model))
            self.create_subckt(element, unique_name)
        else:
            assert False, f"Unmatched generator for this instance {element}, please fix netlist "


