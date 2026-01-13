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
import shutil
import subprocess
from BaseRunner import BaseRunner

class VlogHammerSAT(BaseRunner):
    def __init__(self):
        super().__init__(
            "vloghammer_sat", "yosys", {
                "simulation", "elaboration", "parsing"
            })
        self.submodule = "third_party/tests/vloghammer"

    def get_mode(self, params):
        # SECURITY CHECK: Only run if the 'vloghammer' tag is present
        if "tags" not in params or "vloghammer" not in params['tags']:
            return None

        return super().get_mode(params)

    def prepare_run_cb(self, tmp_dir, params):
        test_name = params['name']

        basename = os.path.basename(test_name)
        job_name = basename.replace("vloghammer_", "").replace(".sv", "")

        third_party_dir = os.environ['THIRD_PARTY_DIR']
        vloghammer_dir = os.path.join(third_party_dir, 'tests', 'vloghammer')
        if not os.path.isdir(vloghammer_dir):
             vloghammer_dir = os.path.join(third_party_dir, 'test', 'vloghammer')

        run_script = os.path.join(tmp_dir, "run.sh")

        with open(run_script, 'w') as f:
            f.write("set -x\n")
            f.write(f"cd {vloghammer_dir}\n")
            f.write(f"make syn_yosys DEPS=1 RTL_LIST={job_name}\n")
            f.write(f"make check_yosys DEPS=1 RTL_LIST={job_name}\n")
            f.write(f"cat check_yosys/{job_name}.txt\n")


        self.cmd = ['sh', run_script]

    def is_success_returncode(self, rc, params):
        return rc == 0
