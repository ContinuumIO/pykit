# -*- coding: utf-8 -*-

"""
State for pykit pipeline.
"""

from __future__ import print_function, division, absolute_import
from os.path import join, abspath, dirname
import copy

from pykit.analysis import cfa
from pykit.lower import lower_calls, lower_errcheck
from pykit.codegen import resolve_typedefs, llvm

root = abspath(dirname(__file__))

# ______________________________________________________________________
# Pipeline

pipeline_stages = [
    "pipeline.analyze",
    "pipeline.optimize",
    "pipeline.lower",
    "pipeline.codegen"
]

pipeline_analyze = ["passes.cfa"]
pipeline_optimize = []
pipeline_lower = ["passes.lower_calls", "passes.lower_errcheck"]
pipeline_codegen = ["passes.resolve_typedefs", "passes.codegen"]

# ______________________________________________________________________
# Passes

default_passes = {
    # Analyze
    "passes.cfa": cfa,

    # Optimize

    # Lower
    "passes.lower_calls": lower_calls,
    "passes.lower_errcheck": lower_errcheck,

    # Codegen
    "passes.resolve_typedefs": resolve_typedefs,
    "passes.codegen": None, # Use codegen.install()
}

# ______________________________________________________________________

def fresh_env():
    """Get a fresh environment"""
    env = {}

    # Pipeline
    env["pipeline.stages"]   = list(pipeline_stages)
    env["pipeline.analyze"]  = list(pipeline_analyze)
    env["pipeline.optimize"] = list(pipeline_optimize)
    env["pipeline.lower"]    = list(pipeline_lower)
    env["pipeline.codegen"]  = list(pipeline_codegen)

    # Passes
    env.update(default_passes)

    # Runtime
    env["runtime.librarypaths"] = []
    env["runtime.libraries"] = []

    # Libraries
    env["library.threads"] = None

    # Misc data
    # { Long : Int32, ...}
    env['types.typedefmap'] = dict(resolve_typedefs.typedef_map)
    env["codegen.impl"] = None
    env["codegen.cache"] = {}

    return env

def copy(env):
    """Return a copy of this environment"""
    return copy.deepcopy(env)