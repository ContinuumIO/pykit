# -*- coding: utf-8 -*-

"""
Resolve typedefs. This turns portable into unportable IR for code generator.
"""

import struct
from functools import partial

from pykit import types as t
from pykit.utils import hashable

types = (t.Char, t.Short, t.Int, t.Long, t.LongLong,
         t.UChar, t.UShort, t.UInt, t.ULong, t.ULongLong)
codes = ('c', 'h', 'i', 'l', 'Q') * 2

typedef_map = {} # { Long: Int32, ... }

for code, typedef in zip(codes, types):
    size = struct.calcsize(code)
    if typedef.type.unsigned:
        concrete_type = getattr(t, 'UInt%d' % (size * 8))
    else:
        concrete_type = getattr(t, 'Int%d' % (size * 8))

    typedef_map[typedef] = concrete_type

def reconstruct_type(ty, typemap):
    reconstruct = partial(reconstruct_type, typemap=typemap)
    if isinstance(ty, list):
        return list(map(reconstruct, ty))
    if not isinstance(ty, t.Type):
        return ty
    elif ty in typemap:
        return typemap[ty]
    else:
        ctor = type(ty)
        return ctor(*map(reconstruct, ty))

def run(func, env):
    """env['types.typedefmap'] should be installed"""
    typemap = env['types.typedefmap']
    func.type = reconstruct_type(func.type, typemap)
    for arg in func.args:
        arg.type = reconstruct_type(arg.type, typemap)
    for op in func.ops:
        op.type = reconstruct_type(op.type, typemap)