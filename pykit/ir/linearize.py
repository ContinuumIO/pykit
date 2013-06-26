# -*- coding: utf-8 -*-

"""
Create a linearized form of the IR.
"""

from __future__ import print_function, division, absolute_import

def linearize(func):
    """
    Return a linearized from of the IR and a dict mapping basic blocks to
    offsets.
    """
    result = []
    blockstarts = {} # { block_label : instruction offset }
    for block in func.blocks:
        blockstarts[block.name] = len(result)
        result.extend(iter(block))
    return result, blockstarts