# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import
from pykit.tests import *
from pykit.lower import lower_errcheck

class TestExcCheckLowering(SourceTestCase):

    source = """
        extern float external(float);

        float testfunc(float a) {
            (void) check_error(0, 0);
            return 2.0;
        }
    """

    def test_check_error_costful(self):
        lower_errcheck.lower_costful(self.f)
        self.eq(findop(self.f, 'ret').args[0], Undef(types.Float32))
        self.eq(opcodes(self.f)[:3], ['eq', 'cbranch', 'ret'])
        assert not findop(self.f, 'check_error')