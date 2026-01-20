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


class Sv2v_zachjs(BaseRunner):
    def __init__(self):
        super().__init__(
            "zachjs-sv2v", "zachjs-sv2v",
            {"preprocessing", "parsing", "elaboration"})

        self.submodule = "third_party/tools/zachjs-sv2v"
        self.url = f"https://github.com/zachjs/sv2v/tree/{self.get_commit()}"

    def prepare_run_cb(self, tmp_dir, params):
        run = os.path.join(tmp_dir, "run.sh")
        cmd = [self.executable]

        for incdir in params['incdirs']:
            cmd.append('-I' + incdir)

        for define in params['defines']:
            cmd.append('-D' + define)

        cmd += params['files']
        
        # Prepare wrapper script
        with open(run, 'w') as f:
            f.write('set -e\n')
            f.write('set -x\n')
            
            # Construct command string
            cmd_str = " ".join(cmd)
            
            # Run sv2v and save output
            f.write(f'{cmd_str} > syn.v\n')
            f.write('cat syn.v\n') # Print to stdout for log capture
            
            # Verismith Integration
            is_verismith = "tags" in params and "verismith" in params["tags"]
            if is_verismith:
                bin_path = Verismith.find_binary()
                if bin_path:
                    test_file = params['files'][0]
                    # sv2v outputs Verilog, so we check equivalence
                    abs_test_file = os.path.abspath(test_file)
                    abs_syn_file = "syn.v"
                    
                    equiv_cmd = Verismith.get_equiv_cmd(bin_path, abs_test_file, abs_syn_file)
                    equiv_cmd_str = " ".join(equiv_cmd)
                    f.write(f"{equiv_cmd_str}\n")
                else:
                    f.write("echo 'Verismith binary not found, skipping equiv check'\n")

        self.cmd = ['sh', run]

    def get_version(self):
        version = super().get_version()

        # return it with our custom prefix and without the trailing newline
        return "zachjs-" + version.rstrip()
