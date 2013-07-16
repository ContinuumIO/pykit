# -*- coding: utf-8 -*-

"""
Visitor and transformer helpers.
"""

from __future__ import print_function, division, absolute_import
import inspect

def transform(obj, function, handlers=None):
    """Transform a bunch of operations"""
    obj = combine(obj, handlers)
    for op in function.ops:
        fn = getattr(obj, 'op_' + op.opcode, None)
        if fn is not None:
            result = fn(op)
            if result is not None and result is not op:
                op.replace_with(result)

def visit(obj, function, handlers=None):
    """Visit a bunch of operations"""
    obj = combine(obj, handlers)
    for op in function.ops:
        fn = getattr(obj, 'op_' + op.opcode, None)
        if fn is not None:
            fn(op)

# ______________________________________________________________________

class Combinator(object):
    """
    Combine several visitors/transformers into one.
    One can also use dicts wrapped in pykit.utils.ValueDict.
    """

    def __init__(self, visitors, prefix='op_', index=None):
        self.index = _build_index(visitors, prefix)
        if index:
            assert not set(index) & set(self.index)
            self.index.update(index)

    def __getattr__(self, attr):
        try:
            return self.index[attr]
        except KeyError:
            raise AttributeError(attr)


def _build_index(visitors, prefix):
    """Build a method table of method names starting with `prefix`"""
    index = {}
    for visitor in visitors:
        for attr, method in inspect.getmembers(visitor):
            if attr.startswith(prefix):
                if attr in index:
                    raise ValueError("Handler %s not unique!" % attr)
                index[attr] = method

    return index

def combine(visitor, handlers):
    """Combine a visitor/transformer with a handler dict ({'name': func})"""
    if handlers:
        visitor = Combinator([visitor], index=handlers)
    return visitor