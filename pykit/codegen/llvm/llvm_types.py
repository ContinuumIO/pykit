from pykit.types import (Boolean, Integral, Float32, Float64, Struct, Pointer,
                         Function, Void)
from llvm.core import Type, TYPE_FUNCTION

from llvmmath import llvm_support

def llvm_type(type):
    ty = type.__class__
    if ty == Boolean:
        return Type.int(1)
    elif ty == Integral:
        return Type.int(type.bits)
    elif type == Float32:
        return Type.float()
    elif type == Float64:
        return Type.double()
    elif ty == Struct:
        return Type.struct([llvm_type(ftype) for ftype in type.types])
    elif ty == Pointer:
        return Type.pointer(llvm_type(type.base))
    elif ty == Function:
        return Type.function(llvm_type(type.restype),
                             [llvm_type(argtype) for argtype in type.argtypes])
    elif ty == Void:
        return Type.void()
    else:
        raise TypeError("Cannot convert type %s" % (type,))

def ctype(llvm_type):
    return llvm_support.map_llvm_to_ctypes(llvm_type)