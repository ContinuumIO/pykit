# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit import types
from pykit.ir import Builder, Function, Const, Op, verify, from_assembly, ops

testfunc = """
function Float32 testfunc(Int32 %a) {
entry:
    %0 = (Pointer(base=Real(bits=32))) alloca()
    %r = (Int32) mul(%a, %a)
    %1 = (Float32) convert(%r)
    %2 = (Void) store(%1, %0)
    %3 = (Float32) load(%0)
    %4 = (Void) ret(%3)

}
""".strip()

class TestInterp(unittest.TestCase):

    def setUp(self):
        self.f = from_assembly(testfunc)
        self.b = Builder(self.f)

    def test_replace(self):
        entry = self.f.get_block('entry')
        for op in entry:
            if op.opcode == ops.convert:
                r, = op.args
                t = self.b.add(types.Int32, [r, r], result="temp")
                c = self.b.convert(types.Float32, [t], result=op.result)
                op.replace([t, c])
                break

        result = [(op.opcode, op.result) for op in entry]
        assert result == [('alloca', '0'), ('mul', 'r'), ('add', 'temp'),
                          ('convert', '1'), ('store', '2'), ('load', '3'),
                          ('ret', '4')]