# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit.ir import from_assembly

source = """
function Float64 multiply(Float64 %a, Int32 %b) {
entry:
    %result = (Float64 *) alloca()
    %discard = (Void) jump(%cond)

cond:
    %count = (Int32) phi([%entry, %loop], [0, %incr])
    %stop = (Bool) lt(%count, 10)
    %discard1 = (Void) cbranch(%stop, %loop, %exit)

loop:
    %incr = (Int32) add(%count, 1)
    %res = (Float64) load(%result)
    %tmp = (Float64) add(%res, %a)
    %discard2 = (Void) store %tmp %result
    %discard3 = (Void) jump(%cond)

exit:
    %discard3 = (Void) ret %result
}
"""

# mod = from_assembly(source)

class TestInterp(unittest.TestCase):
    def test_loop(self):
        pass # TODO: