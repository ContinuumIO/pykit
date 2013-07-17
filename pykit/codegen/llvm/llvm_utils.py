# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import
import ctypes

from .llvm_types import ctype

import llvm.ee
import llvm.passes
import llvm.core

# ______________________________________________________________________

def verify(mod_or_func):
    mod_or_func.verify()

def target_machine(opt=3):
    features = '-avx'
    return llvm.ee.TargetMachine.new(
        opt=opt, cm=llvm.ee.CM_JITDEFAULT, features=features)

def module(name):
    return llvm.core.Module.new(name)

def execution_engine(llvm_module, target_machine):
    return llvm.ee.EngineBuilder.new(llvm_module).create(target_machine)

def optimize(llvm_module, target_machine, opt=3, inline=1000):
    has_loop_vectorizer = llvm.version >= (3, 2)
    passmanagers = llvm.passes.build_pass_managers(
        target_machine, opt=opt, inline_threshold=inline,
        loop_vectorize=has_loop_vectorizer, fpm=False)
    passmanagers.pm.run(llvm_module)

def pointer_to_func(engine, lfunc):
    addr = engine.get_pointer_to_function(lfunc)
    return ctypes.cast(addr, ctype(lfunc.type.pointee))

# ______________________________________________________________________

handle = lambda llvm_value: llvm_value._ptr

def link_module(engine, src_module, dst_module, preserve=False):
    """
    Link a source module into a destination module while preserving the
    execution engine's global mapping of pointers.
    """
    dst_module.link_in(src_module, preserve=preserve)
    ptr = lambda gv: handle(engine).getPointerToGlobalIfAvailable(handle(gv))

    def update_gv(src_gv, dst_gv):
        if ptr(src_gv) != 0 and ptr(dst_gv) == 0:
            engine.add_global_mapping(dst_gv, ptr(src_gv))

    # Update function mapping
    for function in src_module.functions:
        dst_lfunc = dst_module.get_function_named(function.name)
        update_gv(function, dst_lfunc)

    # Update other global symbols' mapping
    for src_gv in src_module.global_variables:
        dst_gv = dst_module.get_global_variable_named(src_gv.name)
        update_gv(src_gv, dst_gv)