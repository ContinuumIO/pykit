# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from pykit.ir import defs
from pykit.tests import *
from pykit.codegen.tests import codegens, llvm_codegen

# ______________________________________________________________________

unops = dict.fromkeys(defs.unary_defs, types.int_set | types.float_set)
unops["!"] |= types.bool_set
unops["~"] -= types.float_set

binops = dict.fromkeys(defs.binary_defs, types.int_set | types.float_set)
for op in set(defs.bitwise) - set(["~"]):
    binops[op] -= types.float_set

# ______________________________________________________________________

def unop(codegen, op, type):
    restype = types.Bool if op == '!' else type
    f = TestFunction("""
        $restype func($type arg) {
            return $op arg;
        }""", restype=restype, type=type, op=op)
    cresult = f.run(codegen, 2)
    iresult = f.interp(2)
    assert cresult == iresult, (cresult, iresult)

def binop(codegen, op, type):
    f = TestFunction("""
        $restype func($type arg1, $type arg2) {
            return arg1 $op arg2;
        }""", restype=type, type=type, op=op)
    cresult = f.run(codegen, 2, 4)
    iresult = f.interp(2, 4)
    assert cresult == iresult, (cresult, iresult)

# ______________________________________________________________________

def load_tests(*args):
    suite = unittest.TestSuite()
    for testfunc, ops in [(unop, unops),
                          (binop, binops)]:
        argstuples = []
        for codegen in codegens:
            for c_op, typeset in ops.iteritems():
                for type in typeset:
                    argstuples.append([codegen, c_op, type])
        mark_test(testfunc, argstuples, suite)
    return suite