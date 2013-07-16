# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit import types
from pykit.parsing import parser

source = """

function Float64 func(Int32 %foo) {
entry:
    %1 = (Float64) foo(%foo)
 block:
    %2 = (Float64) scotch(%foo)

}

function Float64 bar(Int32 %blah) {
entry:
    %1 = (Float64) ham(%foo)
block:
    %2 = (Float64) eggs(%foo)
}

"""

class TestParser(unittest.TestCase):
    def test_parse(self):
        result = parser.from_assembly(source)
        func1, func2 = result.get_function("func"), result.get_function("bar")

        assert func1.name == 'func'
        assert func1.argnames == ["foo"]
        assert func1.type.argtypes == [types.Int32]
        assert len(func1.blocks) == 2

        # Test Ops
        stat, = func1.startblock
        assert stat.result == "1"
        assert stat.type == types.Float64
        assert stat.opcode == "foo"
        assert stat.operands == ["foo"]

        assert func2.name == 'bar'
        assert len(func2.blocks) == 2