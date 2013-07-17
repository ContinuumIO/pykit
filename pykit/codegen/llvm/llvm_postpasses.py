# -*- coding: utf-8 -*-

"""
Postpasses over the LLVM IR.
The signature of each postpass is postpass(env, ee, lmod, lfunc) -> lfunc
"""

from __future__ import print_function, division, absolute_import

import llvmmath
from llvmmath import linking

# ______________________________________________________________________

def postpass_link_math(ee, lmod, lfunc):
    "pykit.math.* -> llvmmath.*"
    replacements = {}
    for lf in lmod.functions:
        if lf.name.startswith('pykit.math.'):
            _, _, name = lf.name.partition('.')
            replacements[lf.name] = name
    del lf # this is dead after linking below

    default_math_lib = llvmmath.get_default_math_lib()
    linker = linking.get_linker(default_math_lib)
    linking.link_llvm_math_intrinsics(ee, lmod, default_math_lib,
                                      linker, replacements)
    return lfunc

# ______________________________________________________________________

def run(lfunc, env):
    postpass_link_math(env["codegen.llvm.engine"], env["codegen.llvm.module"],
                       lfunc)