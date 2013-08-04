# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit.parsing import from_c
from pykit.analysis import cfa
from pykit.ir import findop, opcodes, verify

source = """
#include <pykit_ir.h>

double func_simple(double y) {
    if (y > 5.0)
        y = 5.0;
    else
        y = 2.0;
    return y;
}

double func(double y) {
    Int32 i = 0;

    while (i < 10) {
        if (i > 5) {
            y = i;
        }
        i = i + 1;
    }

    return y;
}
"""

class TestCFA(unittest.TestCase):

    def test_cfg(self):
        mod = from_c(source)
        f = mod.get_function('func_simple')
        verify(f)
        flow = cfa.cfg(f)

        cond_block = findop(f, 'cbranch').block
        self.assertEqual(len(flow[cond_block]), 2)

    def test_ssa(self):
        mod = from_c(source)
        f = mod.get_function('func_simple')
        verify(f)
        self.assertEqual(opcodes(f.startblock),
                         ['alloca', 'store', 'load', 'gt', 'cbranch'])

        # SSA
        CFG = cfa.cfg(f)
        cfa.ssa(f, CFG)

        assert len(f.blocks) == 4
        blocks = list(f.blocks)
        self.assertEqual(opcodes(blocks[0]), ['gt', 'cbranch'])
        self.assertEqual(opcodes(blocks[1]), ['jump'])
        self.assertEqual(opcodes(blocks[2]), ['jump'])
        self.assertEqual(opcodes(blocks[3]), ['phi', 'ret'])

        phi = findop(f, 'phi')
        iblocks, ivals = phi.args
        self.assertEqual(sorted(iblocks), sorted([blocks[1], blocks[2]]))
        self.assertEqual(len(ivals), 2)

    def test_ssa2(self):
        mod = from_c(source)
        f = mod.get_function('func')
        cfa.run(f)
        verify(f)
        codes = opcodes(f)
        self.assertEqual(codes.count('phi'), 3)
