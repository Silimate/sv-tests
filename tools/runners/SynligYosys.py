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


class SynligYosys(BaseRunner):
    def __init__(self):
        super().__init__(
            "yosys-synlig", "yosys-synlig",
            {"preprocessing", "parsing", "elaboration"})

        self.submodule = "third_party/tools/synlig"
        self.url = f"https://github.com/chipsalliance/synlig/tree/{self.get_commit()}"

    def get_mode(self, params):
        unsynthesizable = int(params['unsynthesizable'])
        if unsynthesizable:
            return None
        return super().get_mode(params)

    def prepare_run_cb(self, tmp_dir, params):
        runner_scr = os.path.join(tmp_dir, "scr.sh")
        yosys_scr = os.path.join(tmp_dir, "yosys-script")
        mode = params['mode']
        top = params['top_module'] or None

        # Check for Verismith tag
        is_verismith = "tags" in params and "verismith" in params["tags"]

        if is_verismith:
            # === Verismith Workflow ===
            with open(yosys_scr, "w") as f:
                f.write("plugin -i systemverilog\n")
                f.write("read_systemverilog -nopython -parse -sverilog -nonote -noinfo -nowarning -DSYNTHESIS")

                if mode != "elaboration":
                    f.write(" -parse-only")

                if top is not None:
                    f.write(f' --top-module {top}')

                if mode in ["parsing", "preprocessing"]:
                    f.write(' -noelab')

                for i in params["incdirs"]:
                    f.write(f" -I{i}")

                for d in params["defines"]:
                    f.write(f" -D{d}")

                for fn in params["files"]:
                    f.write(f" {fn}")

                f.write("\n")

                if mode == "elaboration":
                    if top is not None:
                        f.write(f"hierarchy -top \\{top}\n")
                    else:
                        f.write("hierarchy -auto-top\n")

                    f.write(
                        "proc\n"
                        "check\n"
                        "memory_dff\n"
                        "memory_collect\n"
                        "stat\n"
                        "stat\n"
                        "check\n")
                    # Verismith: Force output netlist
                    f.write("write_verilog -noattr syn.v\n")

            with open(runner_scr, "w") as f:
                f.write("set -e\n")
                f.write("set -x\n")
                f.write(f"cat {yosys_scr}\n")
                f.write(f"{self.executable} -s {yosys_scr}\n")

                if mode not in ["preprocessing", "parsing"]:
                    bin_path = Verismith.find_binary()
                    if bin_path:
                        test_file = params['files'][0]
                        abs_test_file = os.path.abspath(test_file)
                        abs_syn_file = "syn.v"
                        cmd = Verismith.get_equiv_cmd(bin_path, abs_test_file, abs_syn_file)
                        f.write(f"{' '.join(cmd)}\n")
                    else:
                        f.write("echo 'Verismith binary not found, skipping equiv check'\n")

        else:
            # === Normal Workflow ===
            with open(yosys_scr, "w") as f:
                f.write("plugin -i systemverilog\n")
                f.write("read_systemverilog -nopython -parse -sverilog -nonote -noinfo -nowarning -DSYNTHESIS")

                if mode != "elaboration":
                    f.write(" -parse-only")

                if top is not None:
                    f.write(f' --top-module {top}')

                if mode in ["parsing", "preprocessing"]:
                    f.write(' -noelab')

                for i in params["incdirs"]:
                    f.write(f" -I{i}")

                for d in params["defines"]:
                    f.write(f" -D{d}")

                for fn in params["files"]:
                    f.write(f" {fn}")

                f.write("\n")

                if mode == "elaboration":
                    if top is not None:
                        f.write(f"hierarchy -top \\{top}\n")
                    else:
                        f.write("hierarchy -auto-top\n")

                    f.write(
                        "proc\n"
                        "check\n"
                        "memory_dff\n"
                        "memory_collect\n"
                        "stat\n"
                        "stat\n"
                        "check\n")

            with open(runner_scr, "w") as f:
                f.write("set -e\n")
                f.write("set -x\n")
                f.write(f"cat {yosys_scr}\n")
                f.write(f"{self.executable} -s {yosys_scr}\n")

        self.cmd = ["sh", runner_scr]
