# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import
from pykit.tests import *
from pykit.analysis import callgraph

class TestCallgraph(SourceTestCase):

    source = """
    int f(int x) {
        return (int) x * 2;
    }

    int g(int x) {
        return (int) ((int) f(x * 2) - 2);
    }
    """
    def test_simple_callgraph(self):
        g = self.m.get_function('g')
        f = self.m.get_function('f')
        G = callgraph.callgraph(g)
        assert f in G.node
        assert g in G.node
        assert f in G.successors(g)
        assert not G.successors(f)

if __name__ == '__main__':
    unittest.main()