# -*- coding: utf-8 -*-

"""
State for pykit pipeline.
"""

from __future__ import print_function, division, absolute_import
from os.path import join, abspath, dirname
import copy

from pykit.analysis import cfa
from pykit.lower import lower_errcheck, lower_calls

root = abspath(dirname(__file__))

pipeline_stages = [
    "pipeline.analyze",
    "pipeline.optimize",
    "pipeline.lower",
    "pipeline.codegen"
]

pipeline_analyze = ["passes.cfa"]
pipeline_optimize = []
pipeline_lower = ["passes.lower_calls", "passes.lower_errcheck"]

def fresh_env():
    """Get a fresh environment"""
    env = {}

    # Pipeline
    env["pipeline.stages"]   = list(pipeline_stages)
    env["pipeline.analyze"]  = list(pipeline_analyze)
    env["pipeline.optimize"] = list(pipeline_optimize)
    env["pipeline.lower"]    = list(pipeline_lower)
    env["pipeline.codegen"]  = []

    # Passes
    env["passes.cfa"] = cfa

    # Runtime
    env["runtime.librarypaths"] = []
    env["runtime.libraries"] = []

    # Libraries
    env["library.threads"] = None

    # Codegen
    env["codegen"] = None

    return env

def install_llvm_codegen(env, opt=3):
    from pykit.codegen import llvm
    from pykit.codegen.llvm import llvm_postpasses

    env["pipeline.codegen"].extend([llvm, llvm_postpasses])
    env["codegen.llvm.opt"] = opt
    env["codegen.llvm.engine"] = None
    env["codegen.llvm.module"] = None
    env["codegen.llvm.machine"] = llvm.target_machine(opt)

def copy(env):
    """Return a copy of this environment"""
    return copy.deepcopy(env)