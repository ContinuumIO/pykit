# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import
from pykit.tests import *
from pykit.analysis import loop_detection

class Unnested(SourceTestCase):
    source = """
    int single(int i) {
        double a;
        for (i = 0; i < 5; i = i + 1) {
            if (i < 2)
                a = i;
        }
        while (i < 2)
            a = 0;

        return (int) a;
    }
    """

    def test_unnested(self):
        loops = loop_detection.find_natural_loops(self.f)
        assert len(loops) == 2
        assert len(loops[0].children) == 0
        assert len(loops[1].children) == 0
        assert len(loops[0].blocks) >= 4
        assert len(loops[1].blocks) >= 2

class Nested(SourceTestCase):
    source = """
    int nested(int i) {
        for (i = 0; i < 5; i = i + 1)
            while (i < 2)
                if (i)
                    while (i < 2)
                        i = 1;
        return i;
    }
    """

    def test_nested(self):
        loops = loop_detection.find_natural_loops(self.f)
        for i in range(3):
            loop, = loops
            loops = loop.children