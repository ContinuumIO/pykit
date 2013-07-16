# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit import from_c, environment, types
from pykit.ir import *
from pykit.analysis import cfa, defuse

class SourceTestCase(unittest.TestCase):

    source = None
    funcname = None
    cfa = True
    verify = True

    def setUp(self):
        self.m = from_c(self.source)
        verify(self.m)
        if self.cfa:
            for function in self.m.functions.values():
                cfa.run(function)
                verify(function)
            verify(self.m)

        if len(self.m.functions) == 1:
            self.funcname, = self.m.functions

        if self.funcname:
            self.f = self.m.get_function(self.funcname)
            self.b = Builder(self.f)
            self.entry = self.f.startblock

        self.env = environment.fresh_env()

        self.eq = self.assertEqual