# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit.parsing import cirparser
from pykit.ir import verify, interp

source = """
int myglobal = 10;

int myfunc(float x) {
    int y;
    int i = 10;

    y = 4;
    while (y < i) {
        y = (int) y + 1;
        (int) print_(myglobal);
    }

    return y + 2;
}
"""

class TestParser(unittest.TestCase):
    def test_parse(self):
        mod = cirparser.from_c(source)
        verify(mod)
        func = mod.get_function('myfunc')
        result = interp.run(func, args=[10.0])
        self.assertEqual(result, 12)