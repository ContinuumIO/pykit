# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
import textwrap
from pykit.ir import parser, pretty
from pykit.core.value import Module, Function, Block, op, GlobalValue

class MockType(object):
    return_type = None
    args = []

func = Function('func', type=MockType(),
                blocks=[Block('block1', instrs=[op("add", None, [], "foo")])])
program = Module(globals={'foo': GlobalValue('foo', None)},
                 functions={'func': func})

class TestParser(unittest.TestCase):
    def test_pretty(self):
        result = pretty.pretty_format(program)
        assert result == u"""\
global %foo = None

function func None() {
block1:
    %foo = (None) add()
}
"""