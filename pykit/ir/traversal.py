# -*- coding: utf-8 -*-

"""
Visitor and transformer helpers.
"""

from __future__ import print_function, division, absolute_import

def transform(obj, function):
    """Transform a bunch of operations"""
    for op in function.ops:
        fn = getattr(obj, 'op_' + op.opcode, None)
        if fn is not None:
            result = fn(op)
            if result is not None and result is not op:
                op.replace_with(result)

def visit(obj, function):
    """Visit a bunch of operations"""
    for op in function.ops:
        fn = getattr(obj, 'op_' + op.opcode, None)
        if fn is not None:
            fn(op)