# -*- coding: utf-8 -*-

"""
Pass helpers.
"""

from __future__ import print_function, division, absolute_import
from pykit.ir import defs, combine
from pykit.ir.builder import OpBuilder, Builder
from pykit.utils import prefix as prefix_, mergedicts

class FunctionPass(object):
    """
    Can be used from visitors or transformers, holds a builder and opbuilder.
    """

    opbuilder = OpBuilder()

    def __init__(self, func):
        self.func = func
        self.builder = Builder(func)

#===------------------------------------------------------------------===
# Pass to group operations such as add/mul
#===------------------------------------------------------------------===

def opgrouper(visitor, prefix='op_'):
    """
    Create dispatchers for unary, binary and compare opcodes to op_unary,
    op_binary and op_compare.
    """
    handlers = mergedicts(unop_handlers(visitor.op_unary, prefix),
                          binop_handlers(visitor.op_binary, prefix),
                          compare_handlers(visitor.op_compare, prefix))
    return combine(visitor, handlers)

def unop_handlers(handler, prefix='op_'):
    return dict.fromkeys(prefix_(defs.unary, prefix), handler)

def binop_handlers(handler, prefix='op_'):
    return dict.fromkeys(prefix_(defs.binary, prefix), handler)

def compare_handlers(handler, prefix='op_'):
    return dict.fromkeys(prefix_(defs.compare, prefix), handler)