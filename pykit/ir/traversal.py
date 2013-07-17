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

def vvisit(obj, function, argloader=None, valuemap=None):
    """
    Visit a bunch of operations and track values. Uses ArgLoader to
    resolve Op arguments.
    """
    argloader = argloader or ArgLoader()
    valuemap = {} if valuemap is None else valuemap

    for arg in function.args:
        valuemap[arg.result] = obj.op_arg(arg)

    for block in function.blocks:
        obj.blockswitch(argloader.load_Block(block, valuemap))
        for op in block.ops:
            fn = getattr(obj, 'op_' + op.opcode, None)
            if fn is not None:
                args = argloader.load(op, valuemap)
                result = fn(op, *args)
                valuemap[op.result] = result

    return valuemap

class ArgLoader(object):
    """Resolve Operation arguments"""

    def load(self, op, valuemap):
        return self.load_args(op.args, valuemap)

    def load_args(self, args, valuemap):
        from pykit.ir import Value

        for arg in args:
            if isinstance(arg, Value):
                yield getattr(self, 'load_' + type(arg).__name__)(arg, valuemap)
            elif isinstance(arg, list):
                yield [self.load_args(arg, valuemap) for arg in arg]
            else:
                yield arg

    def load_Block(self, arg, valuemap):
        return arg

    def load_FuncArg(self, arg, valuemap):
        return self.load_Operation(arg, valuemap)

    def load_Constant(self, arg, valuemap):
        return arg.const

    def load_GlobalValue(self, arg, valuemap):
        raise NotImplementedError

    def load_Operation(self, arg, valuemap):
        if arg.result not in valuemap:
            raise NameError(arg.result, valuemap)
        return valuemap[arg.result]

# ______________________________________________________________________

class Combinator(object):
    """
    Combine several visitors/transformers into one.
    One can also use dicts wrapped in pykit.utils.ValueDict.
    """

    def __init__(self, visitors, prefix='op_', index=None):
        self.visitors = visitors
        self.index = _build_index(visitors, prefix)
        if index:
            assert not set(index) & set(self.index)
            self.index.update(index)

    def __getattr__(self, attr):
        try:
            return self.index[attr]
        except KeyError:
            if len(self.visitors) == 1:
                # no ambiguity
                return getattr(self.visitors[0], attr)
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