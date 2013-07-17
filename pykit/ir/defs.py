# -*- coding: utf-8 -*-

"""
IR definitions.
"""

from __future__ import print_function, division, absolute_import

import math
import operator

import numpy as np

from pykit.ir import ops
from pykit.utils import invert

#===------------------------------------------------------------------===
# Definitions -> Evaluation function
#===------------------------------------------------------------------===

unary = {
    ops.invert        : operator.inv,
    ops.not_          : operator.not_,
    ops.uadd          : operator.pos,
    ops.usub          : operator.neg,
}

binary = {
    ops.add           : operator.add,
    ops.sub           : operator.sub,
    ops.mul           : operator.mul,
    ops.div           : operator.truediv,
    ops.floordiv      : operator.floordiv,
    ops.lshift        : operator.lshift,
    ops.rshift        : operator.rshift,
    ops.bitor         : operator.or_,
    ops.bitand        : operator.and_,
    ops.bitxor        : operator.xor,
}

compare = {
    ops.lt            : operator.lt,
    ops.lte           : operator.le,
    ops.gt            : operator.gt,
    ops.gte           : operator.ge,
    ops.eq            : operator.eq,
    ops.noteq         : operator.ne,
    ops.is_           : operator.is_,
    ops.contains      : operator.contains,
}

math_funcs = {
    ops.Sin         : np.sin,
    ops.Asin        : np.arcsin,
    ops.Sinh        : np.sinh,
    ops.Asinh       : np.arcsinh,
    ops.Cos         : np.cos,
    ops.Acos        : np.arccos,
    ops.Cosh        : np.cosh,
    ops.Acosh       : np.arccosh,
    ops.Tan         : np.tan,
    ops.Atan        : np.arctan,
    ops.Atan2       : np.arctan2,
    ops.Tanh        : np.tanh,
    ops.Atanh       : np.arctanh,
    ops.Log         : np.log,
    ops.Log2        : np.log2,
    ops.Log10       : np.log10,
    ops.Log1p       : np.log1p,
    ops.Exp         : np.exp,
    ops.Exp2        : np.exp2,
    ops.Expm1       : np.expm1,
    ops.Floor       : np.floor,
    ops.Ceil        : np.ceil,
    ops.Abs         : np.abs,
    ops.Erfc        : math.erfc,
    ops.Rint        : np.rint,
    ops.Pow         : np.power,
    ops.Round       : np.round,
}

#===------------------------------------------------------------------===
# Definitions
#===------------------------------------------------------------------===

unary_defs = {
    "~": ops.invert,
    "!": ops.not_,
    "+": ops.uadd,
    "-": ops.usub,
}

binary_defs = {
    "+":  ops.add,
    "-":  ops.sub,
    "*":  ops.mul,
    "/":  ops.div,
    "//": ops.floordiv,
    "<<": ops.lshift,
    ">>": ops.rshift,
    "|":  ops.bitor,
    "&":  ops.bitand,
    "^":  ops.bitxor,
}

compare_defs = {
    "<":  ops.lt,
    "<=": ops.lte,
    ">":  ops.gt,
    ">=": ops.gte,
    "==": ops.eq,
    "!=": ops.noteq,
}

unary_opcodes = invert(unary_defs)
binary_opcodes = invert(binary_defs)
compare_opcodes = invert(compare_defs)