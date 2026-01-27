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
import glob


class Verismith:

    @staticmethod
    def get_root_dir():
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    @staticmethod
    def find_binary():
        # Check env var first
        if "VERISMITH_BIN" in os.environ:
            return os.environ["VERISMITH_BIN"]

        # Check default location
        root_dir = Verismith.get_root_dir()
        verismith_dir = os.path.join(
            root_dir, "third_party", "tests", "verismith")

        pattern = os.path.join(
            verismith_dir, "dist-newstyle", "build", "**", "x", "verismith",
            "build", "verismith", "verismith")

        candidates = glob.glob(pattern, recursive=True)
        if candidates:
            return os.path.abspath(candidates[0])

        return None

    @staticmethod
    def get_equiv_cmd(
            bin_path, original_file, synth_file, output_dir="output"):
        return [bin_path, "equiv", "-o", output_dir, original_file, synth_file]
