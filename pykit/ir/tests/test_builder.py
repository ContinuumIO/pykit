# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from functools import partial

from pykit import types
from pykit.ir import Builder, Function, Const, interp, opcodes


loop_expected = """
function Float32 testfunc(Int32 %a) {
entry:
    %3 = (Pointer(base=Int(bits=32, signed=False))) alloca()
    %0 = (Int32) mul(%a, %a)
    %2 = (Void) jump(%start)

start:
    %1 = (Float32) convert(%0)
    %4 = (Void) store(%const(Int32, 5), %3)
    %5 = (Void) jump(%loop.cond)

loop.cond:
    %6 = (Int32) load(%3)
    %7 = (Int32) add(%6, %const(Int32, 2))
    %8 = (Void) store(%7, %3)
    %9 = (Bool) lt(%6, %const(Int32, 10))
    %10 = (Void) cbranch(%9, %loop.body, %loop.exit)

loop.body:
    %12 = (Void) print(%1)
    %11 = (Void) jump(%loop.cond)

loop.exit:
    %13 = (Void) ret(%1)

}
""".strip()

string = lambda s: str(s).strip()

class TestBuilder(unittest.TestCase):

    def setUp(self):
        self.f = Function("testfunc", ['a'],
                          types.Function(types.Float32, [types.Int32]))
        self.b = Builder(self.f)
        self.b.position_at_end(self.f.new_block('entry'))
        self.a = self.f.get_arg('a')

    def test_basic_builder(self):
        v = self.b.alloca(types.Pointer(types.Float32), [])
        result = self.b.mul(types.Int32, [self.a, self.a], result='r')
        c = self.b.convert(types.Float32, [result])
        self.b.store(c, v)
        val = self.b.load(types.Float32, [v])
        self.b.ret(val)
        # print(string(self.f))
        assert interp.run(self.f, args=[10]) == 100

    def test_splitblock(self):
        old, new = self.b.splitblock('newblock')
        with self.b.at_front(old):
            self.b.add(types.Int32, [self.a, self.a])
        with self.b.at_end(new):
            self.b.div(types.Int32, [self.a, self.a])
        self.assertEqual(opcodes(self.f), ['add', 'div'])

    def test_loop_builder(self):
        square = self.b.mul(types.Int32, [self.a, self.a])
        c = self.b.convert(types.Float32, [square])
        self.b.position_after(square)
        _, block = self.b.splitblock('start', terminate=True)
        self.b.position_at_end(block)

        const = partial(Const, type=types.Int32)
        cond, body, exit = self.b.gen_loop(const(5), const(10), const(2))
        with self.b.at_front(body):
            self.b.print(c)
        with self.b.at_end(exit):
            self.b.ret(c)

        self.assertEqual(interp.run(self.f, args=[10]), 100.0)