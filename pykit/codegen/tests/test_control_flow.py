# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import
from pykit.tests import *
from pykit.codegen.tests import codegen_args

source = """
int func(int i, float y) {
    double a;
    for (i = 0; i < 5; i = i + 1) {
        if (i % 2 == 0) {
            y = y * y;
            a = (double) y;
        }
    }
    return (int) a;
}
"""

# @parametrize(codegen_args)
def test_control_flow(codegen):
    f = TestFunction(source)
    cresult = f.run(codegen, 10, 4.2)
    iresult = f.interp(10, 4.2)
    assert cresult == iresult, (cresult, iresult)

test_control_flow(*codegen_args[0])