# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit import types
from pykit.ir import cirparser

source = """
int myfunc(float *x) {
    int y;
    int i = 0;
    float *p;

    y = 4;
    while (y < i) {
        y = (int) y + 1;
        p = 0;
        (int) call_external("myfunc", p);
    }

    return y + (int) 2;
}

"""

asm = """
function Int32 myfunc(Pointer(base=Real(bits=32)) %x) {
entry:
    %p = (Pointer(base=Real(bits=32))) alloca()
    %y = (Int32) alloca()
    %i = (Int32) alloca()
    %0 = (Void) store(%const(Int32, 0), %i)
    %1 = (Void) store(%const(Int32, 4), %y)
    %2 = (Void) jump(%cond)

cond:
    %3 = (Int32) load(%y, %Int(bits=32, signed=False), %alloca, %[])
    %4 = (Int32) load(%i, %Int(bits=32, signed=False), %alloca, %[])
    %temp = (Int32) lt(%3, %4)
    %5 = (Void) cbranch(%temp, %cond, %exit)

body:
    %6 = (Int32) load(%y, %Int(bits=32, signed=False), %alloca, %[])
    %temp = (Int32) add(%6, %const(Int32, 1))
    %7 = (Void) store(%temp, %y)
    %8 = (Void) store(%const(Int32, 0), %p)
    %9 = (Pointer(base=Real(bits=32))) load(%p, %Pointer(base=Real(bits=32)), %alloca, %[])
    %temp = (Int32) call_external(%const(Bytes, "myfunc"), %9)
    %10 = (Void) jump(%cond)

exit:
    %11 = (Int32) load(%y, %Int(bits=32, signed=False), %alloca, %[])
    %temp = (Int32) add(%11, %const(Int32, 2))
    %12 = (Void) ret(%temp)

}
"""

class TestParser(unittest.TestCase):
    def test_parse(self):
        result = cirparser.from_c(source)
        self.assertEqual(str(result).strip(), asm.strip())