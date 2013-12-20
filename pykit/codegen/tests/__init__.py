from pykit.tests import pykitcompile

try:
    import llvm.core
except ImportError:
    llvm_codegen = None
else:
    from pykit.codegen import llvm as llvm_codegen

# ______________________________________________________________________

codegens = []

if llvm_codegen:
    codegens.append(llvm_codegen)

codegen_args = [(codegen,) for codegen in codegens]
