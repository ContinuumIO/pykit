# -*- coding: utf-8 -*-

"""
IR utilities.
"""

from __future__ import print_function, division, absolute_import
import collections
import difflib
import contextlib

from pykit.utils import nestedmap, listify, flatten

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

def index(function, indexed=None):
    """Index the IR, returning { opcode: [operations] }"""
    indexed = indexed or collections.defaultdict(list)
    for block in function.blocks:
        for op in block.ops:
            indexed[op.result].append(op)

    return indexed

# ______________________________________________________________________

def _getops(func_or_block_or_list):
    if isinstance(func_or_block_or_list, list):
        return func_or_block_or_list
    return func_or_block_or_list.ops

def findop(container, opcode):
    """Find the first Operation with the given opcode"""
    for op in _getops(container):
        if op.opcode == opcode:
            return op

def findallops(container, opcode):
    """Find all Operations with the given opcode"""
    found = []
    for op in _getops(container):
        if op.opcode == opcode:
            found.append(op)

    return found

@listify
def opcodes(container):
    """Returns [opcode] for all operations"""
    for op in _getops(container):
        yield op.opcode

@listify
def optypes(container):
    """Returns [type] for all operations"""
    for op in _getops(container):
        yield op.type

# ______________________________________________________________________

def vmap(f, func):
    """
    Apply `f` over all the values in `func`, that is, all Op, Const, FuncArg
    and GlobalValue.
    """
    from . import GlobalValue, Const

    for arg in func.args:
        f(arg)
    for op in func.ops:
        f(op)
        for arg in flatten(op.args):
            if isinstance(arg, (GlobalValue, Const)):
                f(arg)

# ______________________________________________________________________

def diff(before, after):
    """Diff two strings"""
    lines = difflib.Differ().compare(before.splitlines(), after.splitlines())
    return "\n".join(lines)

@contextlib.contextmanager
def passdiff(func):
    """
    with passdiff(func):
        optimizer.run(func)
    """
    before = str(func)
    yield
    after = str(func)
    print(diff(before, after))


