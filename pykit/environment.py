# -*- coding: utf-8 -*-

"""
State for pykit pipeline.
"""

from __future__ import print_function, division, absolute_import
from os.path import join, abspath, dirname
import copy

from pykit.analysis import cfa

root = abspath(dirname(__file__))

def fresh_env():
    """Get a fresh environment"""
    env = {}

    # Pipeline
    env["pipeline.stages"]   = ["pipeline.analyze",
                                "pipeline.optimize",
                                "pipeline.lower",
                                "pipeline.codegen"]
    env["pipeline.analyze"]  = ["passes.cfa"]
    env["pipeline.optimize"] = []
    env["pipeline.lower"]    = ["passes.lower_threads"]
    env["pipeline.codegen"]  = []

    # Passes
    env["passes.cfa"] = cfa

    # Runtime
    env["runtime.librarypaths"] = []
    env["runtime.libraries"] = []

    # Libraries
    env["library.threads"] = None

    return env

def copy(env):
    """Return a copy of this environment"""
    return copy.deepcopy(env)
