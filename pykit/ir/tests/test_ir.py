# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit import types
from pykit.parsing import from_c
from pykit.ir import Builder, ops, opcodes
from pykit.analysis import cfa

source = """
float testfunc(int a) {
    return (float) (a * a);
}
""".strip()

class TestIR(unittest.TestCase):

    def setUp(self):
        self.m = from_c(source)
        self.f = self.m.get_function('testfunc')
        self.b = Builder(self.f)

    def test_replace(self):
        entry = self.f.get_block('entry')
        for op in entry:
            if op.opcode == ops.convert:
                r, = op.args
                t = self.b.add(types.Int32, [r, r])
                c = self.b.convert(types.Float32, [t], result=op.result)
                op.replace([t, c])
                break

        cfa.run(self.f)
        self.assertEqual(opcodes(self.f), ['mul', 'add', 'convert', 'ret'])