#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

import os
import sys
from Verismith import Verismith

from BaseRunner import BaseRunner


class Yosys(BaseRunner):
    def __init__(self):
        super().__init__(
            "yosys", "yosys", {
                "preprocessing", "parsing", "elaboration", "simulation",
                "simulation_without_run"
            })

        self.submodule = "third_party/tools/yosys"
        self.url = f"https://github.com/YosysHQ/yosys/tree/{self.get_commit()}"

    def get_mode(self, params):
        unsynthesizable = int(params['unsynthesizable'])
        if unsynthesizable:
            return None
        return super().get_mode(params)

    def prepare_run_cb(self, tmp_dir, params):
        run = os.path.join(tmp_dir, "run.sh")
        scr = os.path.join(tmp_dir, 'scr.ys')
        mode = params['mode']
        defer = ""
        if mode in ["preprocessing", "parsing"]:
            defer = "-defer"

        nodisplay = ""
        if mode in ["simulation", "simulation_without_run"]:
            nodisplay = "-nodisplay"

        top = params['top_module'] or None
        if (top is not None):
            top_opt = f"-top {top}"
        else:
            top_opt = "-auto-top"

        inc = ""
        for incdir in params['incdirs']:
            inc += f' -I {incdir}'

        defs = ""
        for define in params['defines']:
            defs += f' -D {define}'

        # prepare yosys script
        with open(scr, 'w') as f:
            for svf in params['files']:
                f.write(
                    f'read_verilog {defer} -sv {nodisplay} {inc} {defs} {svf}\n'
                )

            if mode not in ["preprocessing", "parsing"]:
                # prep (without optimizations)
                f.write(
                    f"hierarchy {top_opt}\n"
                    "proc\n"
                    "check\n"
                    "clean\n"
                    "memory_dff\n"
                    "memory_collect\n"
                    "stat\n"
                    "check\n")
            if mode in ['simulation', 'simulation_without_run']:
                f.write("sim -assert\n")

        # prepare wrapper script
        with open(run, 'w') as f:
            f.write('set -e\n')
            f.write('set -x\n')
            f.write(f'cat {scr}\n')
            
            # Verismith Integration
            is_verismith = "tags" in params and "verismith" in params["tags"]
            if is_verismith and mode not in ["preprocessing", "parsing"]:
                 # We need to tell Yosys to output a netlist
                 with open(scr, 'a') as ys:
                     ys.write("write_verilog -noattr syn.v\n")
            
            f.write(f'{self.executable} -Q -T {scr}\n')

            if is_verismith and mode not in ["preprocessing", "parsing"]:
                # Run Equivalence Check
                # Find binary
                bin_path = Verismith.find_binary()
                if bin_path:
                    # Input file is params['files'][0] (assuming single file test)
                    test_file = params['files'][0]
                    
                    # Create output directory for artifacts
                    # output/verismith/yosys/testname/
                    test_name = params['name']
                    # We are in tmp_dir, so we just run here. 
                    # sv-tests runner infrastructure handles copying logs.
                    # Use absolute paths for verismith command
                    abs_test_file = os.path.abspath(test_file)
                    abs_syn_file = "syn.v"
                    
                    cmd = Verismith.get_equiv_cmd(bin_path, abs_test_file, abs_syn_file)
                    cmd_str = " ".join(cmd)
                    f.write(f"{cmd_str}\n")
                else:
                    f.write("echo 'Verismith binary not found, skipping equiv check'\n")

        self.cmd = ['sh', run]

    def get_version_cmd(self):
        return [self.executable, "-V"]

    def get_version(self):
        version = super().get_version()

        return " ".join([self.name, version.split()[1]])
