# -*- coding: utf-8 -*-

"""
Directed graphs and a few algorithms.
"""

from __future__ import print_function, division, absolute_import
import collections

class Graph(object):
    """
    Directed graph. Supports iteration and indexing.

        edges: adjacency matrix, { src: {dst} }
    """

    def __init__(self, edges=None):
        self.edges = edges or collections.defaultdict(set)

    def add_edge(self, src, dst):
        self.edges[dst] # make sure to add 'dst' as a node
        self.edges[src].add(dst)

    def __getitem__(self, item):
        return self.edges[item]

    def __iter__(self):
        return iter(self.edges)

    @property
    def T(self):
        return transpose(self.edges)

    def __str__(self):
        result = [".. digraph: somegraph"]
        for src, dsts in self.edges.iteritems():
            for dst in dsts:
                result.append("    %s -> %s" % (src, dst))
        return "\n".join(result)

    def view(self):
        import matplotlib.pyplot as plt
        networkx.draw(_networkx(self))
        plt.show()



def transpose(graph):
    """
    Return transposed graph (inverted edges)
    """
    transposed = Graph()
    for src in graph:
        for dst in graph[src]:
            transposed.add_edge(dst, src)

    return transposed

def toposort(graph):
    """
    Return a topological sort of the dag.
    """
    result = []
    seen = set()            # seen but unfinished nodes, for verification
    explored = set()        # processed nodes (in result list)
    pending = list(graph)   # things to process

    while pending:
        w = pending.pop()
        if w in explored:
            continue

        seen.add(w)
        children = []
        for n in graph[w]:
            if n not in explored:
                if n in seen:
                    raise ValueError("Not a DAG: (%s, %s)" % (w, n))
                children.append(n)

        if children:
            pending.append(w)
            pending.extend(children) # Process children first
        else:
            explored.add(w)
            result.append(w)

    return result[::-1]

# ______________________________________________________________________

try:
    import networkx # I think this should be a hard dependency
except ImportError:
    class networkx(object):
        def __getattr__(self):
            import networkx # Raise exception

def _networkx(graph):
    G = networkx.DiGraph()
    for src in graph:
        for dst in graph[src]:
            G.add_edge(src, dst)

    return G

def strongly_connected_components(G):
    """Return nodes in strongly connected components of graph."""
    return networkx.strongly_connected_components(_networkx(G))

def condensation(graph, scc=None):
    """
    Return a condensation graph (a DAG). Cycles are condensed into single
    nodes
    """
    return networkx.condensation(_networkx(graph), scc)