import ctypes
from llvmpy.api import llvm
from .llvm_utils import llvm_context


unknown_type = llvm.StructType.create(llvm_context, "unknown")
unknown_ptr = llvm.PointerType.getUnqual(unknown_type)

void = llvm.Type.getVoidTy(llvm_context)
i1 = llvm.Type.getInt1Ty(llvm_context)
i8 = llvm.Type.getInt8Ty(llvm_context)
i16 = llvm.Type.getInt16Ty(llvm_context)
i32 = llvm.Type.getInt32Ty(llvm_context)
i64 = llvm.Type.getInt64Ty(llvm_context)

f32 = llvm.Type.getFloatTy(llvm_context)
f64 = llvm.Type.getDoubleTy(llvm_context)

if ctypes.c_ssize_t == ctypes.c_int32:
    py_ssize_t = i32
else:
    py_ssize_t = i64

string = llvm.PointerType.getUnqual(i8)
void_ptr = string
