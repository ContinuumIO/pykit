# -*- coding: utf-8 -*-

"""
Verify the validity of pykit IR.
"""

from __future__ import print_function, division, absolute_import

from pykit.ir import Value, Function, Operation, Block, Constant
from pykit.utils import match

class VerifyError(Exception):
    """Raised when we fail to verify IR"""

def unique(items):
    seen = set()
    for item in items:
        if item in seen:
            raise VerifyError("Item not unique", item)
        seen.add(item)

@match
def verify(func, env=None):
    # Verify function arguments
    # ...

    # Verify block labels
    unique(block.name for block in func.blocks)

    # Verify block order
    # ...

    # Verify Op uniqueness
    unique(op for block in func.blocks for op in block)
    unique(op.result for block in func.blocks for op in block)

    # Verify value mapping
    for block in func.blocks:
        for op in block:
            assert op.result in func.values

@verify.case(op=Operation)
def verify(op, env=None):
    assert op.block is not None, op
    assert op.result is not None, op
    for arg in op.args:
        assert isinstance(arg, (Operation, Constant))