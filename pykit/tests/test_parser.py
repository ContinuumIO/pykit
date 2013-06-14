# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit import parser

source = """

function func(int %foo) {
entry:
    %1 = (double) foo(int %foo)
 block:
    %2 = (double) scotch(int %foo)

}

function bar(int %blah) {
entry:
    %1 = (double) ham(int %foo)
block:
    %2 = (double) eggs(int %foo)
}

"""

class TestParser(unittest.TestCase):
    def test_parse(self):
        result = parser.from_assembly(source)
        func1, func2 = result
    
        assert func1.name == 'func'
        assert func1.args == [("int", "foo")]
        assert len(func1.blocks) == 2
        stat = parser.Stat("1", "foo", "double", [("int", "foo")])
        assert func1.blocks[0].stats == [stat], func1.blocks[0].stats
    
        assert func2.name == 'bar'
        assert func2.args == [("int", "blah")]
        assert len(func2.blocks) == 2
        stat = parser.Stat("1", "ham", "double", [("int", "foo")])
        assert func2.blocks[0].stats == [stat], func1.blocks[0].stats