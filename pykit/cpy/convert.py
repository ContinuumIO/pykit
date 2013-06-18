# -*- coding: utf-8 -*-

"""
Lower all conversions between native values <-> objects through the CPython
C-API.
"""

from __future__ import print_function, division, absolute_import
from functools import partial

from pykit import types
from pykit.ir import ops, transform, Op, Const
from pykit.cpy import py_capi
from pykit.utils import match

#===------------------------------------------------------------------===
# Object -> Native
#===------------------------------------------------------------------===

@match
def from_object(b, kind, op):
    raise TypeError("Unsupported conversion from object: %s" % (op.type,))

types.Int()

@from_object.case(kind=types.Int)
def from_object(b, kind, op):
    """convert(Object, obj) -> PyLong_AsLongLong(obj)"""
    fn = "PyLong_AsLongLong" if op.type.signed else "PyLong_AsUnsignedLongLong"
    c = b.gen_call_external(fn, op.args)
    o = b.check_overflow(op.type, [c])
    r = b.convert(op.type, [c], op.result)
    return [c, o, r]

@from_object.case(kind=types.Real)
def from_object(b, kind, op):
    """convert(Object, obj) -> PyFloat_AsDouble(obj)"""
    c = b.gen_call_external("PyFloat_AsDouble", op.args)
    r = b.convert(op.type, [c], op.result)
    return [c, r]

@from_object.case(kind=types.Complex)
def from_object(b, kind, op):
    """convert(Object, obj) -> complex_new(obj.real, obj.imag)"""
    real = b.gen_call_external("PyComplex_RealAsDouble", op.args)
    imag = b.gen_call_external("PyComplex_RealAsDouble", op.args)
    freal = b.convert(op.type, [real])
    fimag = b.convert(op.type, [imag])
    result = b.complex_new(types.Complex(op.type), [freal, fimag], op.result)
    return [real, imag, freal, fimag, result]

#===------------------------------------------------------------------===
# Native -> Object
#===------------------------------------------------------------------===

@match
def to_object(b, kind, op):
    raise TypeError("Unsupported conversion to object: %s" % (op.type,))

@from_object.case(kind=types.Int)
def to_object(b, kind, op):
    """convert(Int, arg) -> PyLong_FromLongLong(arg)"""
    fn = "PyLong_FromLongLong" if op.type.signed else "PyLong_FromUnsignedLongLong"
    return b.gen_call_external(fn, op.args, op.result)

@from_object.case(kind=types.Real)
def to_object(b, kind, op):
    """convert(Real, arg) -> PyFloat_AsDouble(arg)"""
    c = b.gen_call_external("PyFloat_AsDouble", op.args)
    r = b.convert(op.type, [c], op.result)
    return [c, r]

@from_object.case(kind=types.Complex)
def to_object(b, kind, op):
    """convert(Complex, [real, imag]) -> PyComplex_FromDoubles(real, imag)"""
    arg, = op.args
    real = b.getfield(arg, [Const('real')])
    imag = b.getfield(arg, [Const('imag')])
    return b.gen_call_external("PyComplex_FromDoubles", [real, imag], op.result)

#===------------------------------------------------------------------===
# Run
#===------------------------------------------------------------------===

class LowerConversions(object):
    def op_convert(self, op):
        if op.type.is_object and not op.args[0].type.is_object:
            return from_object(op, type(op.type))
        elif op.args[0].type.is_object and not op.type.is_object:
            return to_object(op)

def run(func, env):
    if not func.module.get_global("PyLong_AsLongLong"):
        func.module.link(py_capi.py_c_api_module)
    transform(LowerConversions, func)

# run = partial(transform, LowerConversions)