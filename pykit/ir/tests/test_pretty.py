# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit.ir import pretty, from_assembly

source = u"""\
global %foo = Float64

function Int32 func() {
block1:
    %foo = (Int32) add()

}
"""

program = from_assembly(source)

class TestPretty(unittest.TestCase):
    def test_pretty(self):
        result = pretty.pretty(program)
        self.assertEqual(source.strip(), result.strip())