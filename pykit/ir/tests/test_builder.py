# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit import types
from pykit.ir import builder, value

class TestBuilder(unittest.TestCase):
    def test_builder(self):
        f = value.Function("testfunc")
        b = builder.Builder(f)
        var = b.alloca(types.Float32, result='%0')
        val = b.load(types.Float32, ["%0"])
