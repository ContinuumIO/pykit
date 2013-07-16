from llvmpy.api import llvm

def null(ty):
    return llvm.Constant.getNullValue(ty)

def integer(ty, val):
    return llvm.ConstantInt.get(ty, val)
