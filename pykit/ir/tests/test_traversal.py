# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from pykit.ir import visit, combine, Op
from pykit.tests import *

class SampleVisitor(object):
    def __init__(self):
        self.recorded = []

    def op_mul(self, op):
        self.recorded.append(op.opcode)

class TestTraversal(SourceTestCase):

    source = """
        float testfunc(int a) {
            return (float) (a * a);
        }
    """

    def test_combinator(self):
        visitor = SampleVisitor()
        def op_blah(op):
            visitor.recorded.append(op.opcode)

        comb = combine(visitor, {'op_blah': op_blah})
        with self.b.at_front(self.entry):
            self.b.emit(Op('blah', None, []))
        visit(comb, self.f)
        self.eq(visitor.recorded, ['blah', 'mul'])