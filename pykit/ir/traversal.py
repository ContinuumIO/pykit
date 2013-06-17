# -*- coding: utf-8 -*-

"""
Visitor and transformer helpers.
"""

from __future__ import print_function, division, absolute_import
import collections

def transform(obj, function):
    """Transform a bunch of operations"""
    for block in function.blocks:
        for op in block.instrs:
            fn = getattr(obj, 'op_' + op.opcode, None)
            if fn is not None:
                result = fn(op)
                if result is not None and result is not op:
                    op.replace_with(result)

def visit(obj, function):
    """Visit a bunch of operations"""
    for block in function.blocks:
        for op in block.instrs:
            fn = getattr(obj, 'op_' + op.opcode, None)
            if fn is not None:
                fn(op)

def index(function, indexed=None):
    """Index the IR, returning { opcode: [operations] }"""
    indexed = indexed or collections.defaultdict(list)
    for block in function.blocks:
        for op in block.instrs:
            indexed[op.result].append(op)

    return indexed