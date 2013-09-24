# -*- coding: utf-8 -*-

"""
Detect natural loops based on dominators. Recall that `a dom b` if every
path from the root to `b` must go through `a` first.

This only identifies only natural loops, i.e. where the loop head dominates
the loop tail.

A better algorithm is shown in [1], which does only a single DFS and handles
irreducible CFGs (CFGs with unstructured control flow). A CFG is reducible
if it

[1]: A New Algorithm for Identifying Loops in Decompilation
"""

from __future__ import print_function, division, absolute_import
from pykit.analysis import cfa

class Loop(object):
    """
    Loop-nesting tree in the loop-nesting forest.

        blocks: contained blocks in depth-first spanning tree order
        children: loops nested within the loop
    """

    def __init__(self, blocks=None, children=None):
        self.blocks = blocks or []
        self.children = children or []

    @property
    def head(self):
        return self.blocks[0]

    @property
    def tail(self):
        return self.blocks[-1]


def find_natural_loops(func, cfg=None):
    """Return a loop nesting forest for the given function ([Loop])"""
    cfg = cfg or cfa.cfg(func)
    dominators = cfa.compute_dominators(func, cfg)

    loops = []
    loop_stack = []
    for block in func.blocks:
        ### Look for incoming back-edge
        for pred in cfg.predecessors(block):
            if block in dominators[pred]:
                # We dominate an incoming block, this means there is a
                # back-edge (pred, block)
                loop_stack.append(Loop([block]))

        ### Populate Loop
        if loop_stack:
            loop = loop_stack[-1]
            head = loop.blocks[0]
            if head in dominators[block] and head != block:
                # Dominated by loop header, add
                loop.blocks.append(block)

            if head in cfg[block]:
                loop_stack.pop()
                if loop_stack:
                    # update outer loop
                    loop_stack[-1].blocks.extend(loop.blocks)
                    loop_stack[-1].children.append(loop)
                else:
                    # outermost loop, add to forest
                    loops.append(loop)

    assert not loop_stack
    return loops

def flatloops(loop_forest):
    """Return a flat iterator of all loops in the forest"""
    for loop in loop_forest:
        yield loop
        for child in flatloops(loop.children):
            yield child