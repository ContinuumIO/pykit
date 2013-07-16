# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit.adt import Graph, toposort

def makedag():
    dag = Graph()
    dag.add_edge('a', 'b')
    dag.add_edge('b', 'c')
    dag.add_edge('c', 'd')
    dag.add_edge('d', 'e')
    dag.add_edge('a', 'd')
    dag.add_edge('d', 'e')
    dag.add_edge('b', 'e')
    return dag

class TestGraph(unittest.TestCase):
    def test_toposort(self):
        dag = makedag()
        result = toposort(dag)
        self.assertEqual(result, list('abcde'))

    def test_error_toposort(self):
        dag = makedag()
        dag.add_edge('d', 'b')
        self.assertRaises(ValueError, toposort, dag)