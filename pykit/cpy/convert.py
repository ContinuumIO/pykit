# -*- coding: utf-8 -*-

"""
Lower all conversions between native values <-> objects through the CPython
C-API.
"""

from __future__ import print_function, division, absolute_import
from functools import partial

from pykit import types
from pykit.ir import transform, Op, Const

def from_object(op):
    dst_type = op.type
    if dst_type.is_int:
        c = Op("call_external", types.LongLong, ["PyLong_AsLongLong", op.args])
        e = Op("cpy_checkexc", types.Void, [c])
        o = Op("check_overflow", dst_type, [c])
        d = Op("convert", dst_type, [c])
        return [c, e, o, d]


class LowerConversions(object):
    def op_convert(self, op):
        if op.type.is_object and not op.args[0].type.is_object:
            return from_object(op)
        elif op.args[0].type.is_object and not op.type.is_object:
            return to_object(op)

run = partial(transform, LowerConversions)