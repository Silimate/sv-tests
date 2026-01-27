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

        # Common Yosys script generation
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

        is_verismith = "tags" in params and "verismith" in params["tags"]
        is_vloghammer = "tags" in params and "vloghammer" in params["tags"]

        if is_vloghammer:
            test_name = params["name"]

            basename = os.path.basename(test_name)
            job_name = basename.replace(".v", "")

            third_party_dir = os.path.abspath(os.environ["THIRD_PARTY_DIR"])
            vloghammer_dir = os.path.join(third_party_dir, "tests", "vloghammer")
            if not os.path.isdir(vloghammer_dir):
                vloghammer_dir = os.path.join(
                    third_party_dir, "test", "vloghammer")


            with open(run, "w") as f:
                f.write("set -x\n")
                f.write(f"cd {vloghammer_dir}\n")
                f.write(f"make syn_yosys DEPS=1 RTL_LIST={job_name}\n")
                f.write(f"make check_yosys DEPS=1 RTL_LIST={job_name}\n")
                f.write(f"cat check_yosys/{job_name}.txt\n")


        elif is_verismith:
            with open(scr, 'w') as f:
                f.write(
                    f'# Verismith test case: evaluation will be done using ./verismith equiv\n'
                )
                for svf in params['files']:
                    f.write(
                        f'read_verilog {defer} {nodisplay} {inc} {defs} {svf}\n'
                    )

                if mode not in ["preprocessing", "parsing"]:
                    f.write("synth;\n")
                    f.write("write_verilog -noattr syn.v\n")

            with open(run, 'w') as f:
                f.write('set -e\n')
                f.write('set -x\n')
                # Verismith: Add root dir to PATH to find 'timeout' shim
                verismith_root = Verismith.get_root_dir()
                f.write(f'export PATH="{verismith_root}:$PATH"\n')
                f.write(f'cat {scr}\n')
                f.write(f'{self.executable} -Q -T {scr}\n')

                if mode not in ["preprocessing", "parsing"]:
                    bin_path = Verismith.find_binary()
                    if bin_path:
                        test_file = params['files'][0]
                        abs_test_file = os.path.abspath(test_file)
                        abs_syn_file = "syn.v"
                        cmd = Verismith.get_equiv_cmd(
                            bin_path, abs_test_file, abs_syn_file)
                        f.write(f"{' '.join(cmd)}\n")
                    else:
                        f.write(
                            "echo 'Verismith binary not found, failing test'\n"
                        )
                        f.write("exit 1\n")

        else:
            # === Normal Workflow ===
            with open(scr, 'w') as f:
                for svf in params['files']:
                    f.write(
                        f'read_verilog {defer} -sv {nodisplay} {inc} {defs} {svf}\n'
                    )

                if mode not in ["preprocessing", "parsing"]:
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

            with open(run, 'w') as f:
                f.write('set -e\n')
                f.write('set -x\n')
                f.write(f'cat {scr}\n')
                f.write(f'{self.executable} -Q -T {scr}\n')

        self.cmd = ['sh', run]

    def get_version_cmd(self):
        return [self.executable, "-V"]

    def get_version(self):
        version = super().get_version()

        return " ".join([self.name, version.split()[1]])


    def is_success_returncode(self, rc, params):
        if "tags" in params and "vloghammer" in params["tags"]:

            if rc != 0:
                return False

            test_name = params["name"]
            basename = os.path.basename(test_name)
            job_name = basename.replace(".v", "")

            third_party_dir = os.path.abspath(os.environ["THIRD_PARTY_DIR"])
            vloghammer_dir = os.path.join(third_party_dir, "tests", "vloghammer")
            if not os.path.isdir(vloghammer_dir):
                vloghammer_dir = os.path.join(
                    third_party_dir, "test", "vloghammer")

            check_dir = os.path.join(vloghammer_dir, "check_yosys")
            err_file = os.path.join(check_dir, f"{job_name}.err")
            txt_file = os.path.join(check_dir, f"{job_name}.txt")

            if os.path.exists(err_file):
                return False

            if os.path.exists(txt_file):
                return True

            return False
        return rc == 0
