# -*- coding: utf-8 -*-

"""
Build a call graph.
"""

from pykit import ir

import networkx as nx

def callgraph(func, graph=None, seen=None):
    """
    Eliminate dead code.
    """
    if seen is None:
        seen = set()
        graph = nx.DiGraph()

    if func in seen:
        return

    graph.add_node(func)
    seen.add(func)

    for op in func.ops:
        if op.opcode == 'call':
            callee, args = op.args
            if isinstance(callee, ir.Function):
                graph.add_edge(func, callee)
                callgraph(callee, graph, seen)

    return graph