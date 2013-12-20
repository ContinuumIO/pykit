# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit import types
from pykit.ir import Function, Builder, Const, opcodes
from pykit.optimizations import local_exceptions

class TestLocalExceptionRewriting(unittest.TestCase):

    def test_exc_rewrite(self):
        func = Function("foo", [], types.Function(types.Void, ()))
        entry = func.new_block("entry")
        catch_block = func.new_block("catch")
        b = Builder(func)

        with b.at_front(entry):
            b.exc_setup([catch_block])
            b.exc_throw(Const(StopIteration, types.Exception))
        with b.at_front(catch_block):
            b.exc_catch([Const(Exception, types.Exception)])

        local_exceptions.run(func, {})
        print(func)


if __name__ == '__main__':
    TestLocalExceptionRewriting('test_exc_rewrite').debug()
    #unittest.main()