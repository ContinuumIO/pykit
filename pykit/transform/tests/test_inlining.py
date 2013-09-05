# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit.analysis import cfa
from pykit.parsing import from_c
from pykit.transform import ret, inline
from pykit.ir import opcodes, findallops, verify, interp

class TestInlining(unittest.TestCase):

    def test_inline(self):
        simple = """
        #include <pykit_ir.h>

        int callee(int i) {
            return i * i;
        }

        int caller(int i) {
            int x = call(callee, list(i));
            return x;
        }
        """
        mod = from_c(simple)
        func = mod.get_function("caller")
        [callsite] = findallops(func, 'call')
        inline.inline(func, callsite)
        cfa.run(func)
        verify(func)
        assert interp.run(func, args=[10]) == 100
        assert len(list(func.blocks)) == 1
        assert opcodes(func) == ['mul', 'ret']

    def test_inline2(self):
        harder = """
        int callee(int i) {
            (void) print(i);
            while (i < 10) {
                i = i + 1;
                return i * 2;
            }
            return i;
        }

        int caller() {
            int x = 4;
            while (x < 10) {
                (void) print(x);
                x = call(callee, list(x));
            }
            return x;
        }
        """
        mod = from_c(harder)
        func = mod.get_function("caller")
        verify(func)
        result = interp.run(func)

        [callsite] = findallops(func, 'call')
        inline.inline(func, callsite)
        cfa.run(func)
        verify(func)

        # TODO: update phi when splitting blocks
        # result2 = interp.run(func)
        # assert result == result2
