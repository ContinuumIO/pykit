# -*- coding: utf-8 -*-

"""
LLVM codegen utilities.
"""

from __future__ import print_function, division, absolute_import

from pykit.utils import make_temper
from . import llvm_postpasses
from . import llvm_codegen
from .llvm_utils import module, target_machine, link_module, execution_engine
from . import llvm_utils
from .. import codegen

name = "llvm"

def install(env, opt=3, llvm_engine=None, llvm_module=None,
            llvm_target_machine=None, temper=make_temper()):
    """Install llvm code generator in environment"""
    llvm_target_machine = llvm_target_machine or target_machine(opt)
    llvm_module = llvm_module or module(temper("temp_module"))
    llvm_engine = llvm_engine or execution_engine(llvm_module,
                                                  llvm_target_machine)

    # -------------------------------------------------
    # Codegen passes

    env["pipeline.codegen"].extend([
        "passes.llvm.postpasses",
        "passes.llvm.ctypes",
    ])

    env["passes.codegen"] = codegen
    env["passes.llvm.postpasses"] = llvm_postpasses
    env["passes.llvm.ctypes"] = get_ctypes

    env["codegen.impl"] = llvm_codegen

    # -------------------------------------------------
    # Codegen state

    env["codegen.llvm.opt"] = opt
    env["codegen.llvm.engine"] = llvm_engine
    env["codegen.llvm.module"] = llvm_module
    env["codegen.llvm.machine"] = llvm_target_machine

def verify(func, env):
    """Verify LLVM function and module"""
    llvm_utils.verify(func)
    llvm_utils.verify(env["codegen.llvm.module"])

def optimize(func, env):
    """Optimize llvm module"""
    llvm_utils.optimize(env["codegen.llvm.module"],
                        env["codegen.llvm.machine"],
                        env["codegen.llvm.opt"])

def get_ctypes(func, env):
    cfunc = llvm_utils.pointer_to_func(env["codegen.llvm.engine"], func)
    env["codegen.llvm.ctypes"] = cfunc

def execute(func, env, *args):
    """Execute llvm function with the given arguments"""
    cfunc = llvm_utils.pointer_to_func(env["codegen.llvm.engine"], func)
    assert len(func.args) == len(args)
    return cfunc(*args)