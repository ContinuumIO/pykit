# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit.environment import fresh_env
from pykit.parsing import from_c
from pykit.transform import ret
from pykit.ir import opcodes

testfunc = """
int func(int i) {
    int y = 2;
    return y;
    while (i < 10) {
        i = i + 1;
        return i * 2;
    }
}
"""

class TestNormalize(unittest.TestCase):
    def test_normalize(self):
        mod = from_c(testfunc)
        func = mod.get_function("func")
        ret.run(func, fresh_env())
        ops = opcodes(func)
        self.assertEqual(ops.count("ret"), 1, ops)