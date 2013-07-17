from functools import partial

from pykit.ir import vvisit, ArgLoader, verify_lowlevel
from pykit.ir import defs, opgrouper
from pykit.types import Bool, Integral, Real, Struct, Pointer, Function, Int64
from pykit.codegen.llvm.llvm_types import llvm_type

import llvm.core as lc
from llvm.core import Type, Constant

#===------------------------------------------------------------------===
# Definitions
#===------------------------------------------------------------------===

compare_float = {
    '>':  lc.FCMP_OGT,
    '<':  lc.FCMP_OLT,
    '==': lc.FCMP_OEQ,
    '>=': lc.FCMP_OGE,
    '<=': lc.FCMP_OLE,
    '!=': lc.FCMP_ONE,
}

compare_signed_int = {
    '>':  lc.ICMP_SGT,
    '<':  lc.ICMP_SLT,
    '==': lc.ICMP_EQ,
    '>=': lc.ICMP_SGE,
    '<=': lc.ICMP_SLE,
    '!=': lc.ICMP_NE,
}

compare_unsiged_int = {
    '>':  lc.ICMP_UGT,
    '<':  lc.ICMP_ULT,
    '==': lc.ICMP_EQ,
    '>=': lc.ICMP_UGE,
    '<=': lc.ICMP_ULE,
    '!=': lc.ICMP_NE,
}

compare_bool = {
    '==' : lc.ICMP_EQ,
    '!=' : lc.ICMP_NE
}

# below based on from npm/codegen

def integer_invert(builder, val):
    return builder.xor(val, Constant.int_signextend(val.type, -1))

def integer_usub(builder, val):
    return builder.sub(Constant.int(val.type, 0), val)

def integer_not(builder, value):
    return builder.icmp(value, Constant.int(value.type, 0), lc.ICMP_NE)

def float_usub(builder, val):
    return builder.sub(Constant.int(val.type, 0), val)

def float_not(builder, val):
    return builder.fcmp(val, Constant.real(val.type, 0), lc.FCMP_ONE)


binop_int  = {
     '+': (lc.Builder.add, lc.Builder.add),
     '-': (lc.Builder.sub, lc.Builder.sub),
     '*': (lc.Builder.mul, lc.Builder.mul),
     '/': (lc.Builder.sdiv, lc.Builder.udiv),
    '//': (lc.Builder.sdiv, lc.Builder.udiv),
     '%': (lc.Builder.srem, lc.Builder.urem),
     '&': (lc.Builder.and_, lc.Builder.and_),
     '|': (lc.Builder.or_, lc.Builder.or_),
     '^': (lc.Builder.xor, lc.Builder.xor),
     '<<': (lc.Builder.shl, lc.Builder.shl),
     '>>': (lc.Builder.ashr, lc.Builder.lshr),
}

binop_float = {
     '+': lc.Builder.fadd,
     '-': lc.Builder.fsub,
     '*': lc.Builder.fmul,
     '/': lc.Builder.fdiv,
    '//': lc.Builder.fdiv,
     '%': lc.Builder.frem,
}

unary_int = {
    '~': integer_invert,
    '!': integer_not,
    "+": lambda builder, arg: arg,
    "-": lc.Builder.neg,
}

unary_float = {
    '!': float_not,
    "+": lambda builder, arg: arg,
    "-": lc.Builder.neg,
}

#===------------------------------------------------------------------===
# Utils
#===------------------------------------------------------------------===

i1, i16, i32, i64 = map(Type.int, [1, 16, 32, 64])

def const_int(type, value):
    return Constant.int(type, value)

const_i32 = partial(const_int, i32)
const_i64 = partial(const_int, i64)
zero = partial(const_int, value=0)
one = partial(const_int, value=1)

def sizeof(builder, ty, intp):
    ptr = Type.pointer(ty)
    null = Constant.null(ptr)
    offset = builder.gep(null, [Constant.int(Type.int(), 1)])
    return builder.ptrtoint(offset, intp)

#===------------------------------------------------------------------===
# Translator
#===------------------------------------------------------------------===

class Translator(object):
    """
    Translate a function in low-level form.
    This means it can only use values of type Bool, Int, Float, Struct or
    Pointer. Values of type Function may be called.
    """

    def __init__(self, func, lfunc, llvm_typer, llvm_module):
        self.func = func
        self.lfunc = lfunc
        self.llvm_type = llvm_typer
        self.lmod = llvm_module
        self.builder = None
        self.phis = [] # [pykit_phi]

    def blockswitch(self, newblock):
        if not self.builder:
            self.builder = lc.Builder.new(newblock)
        self.builder.position_at_end(newblock)

    # __________________________________________________________________

    def op_arg(self, arg):
        return self.lfunc.args[self.func.args.index(arg)]

    # __________________________________________________________________

    def op_unary(self, op, arg):
        genop = { Integral: unary_int, Real: unary_float}[type(op.type)]
        return genop(self.builder, arg, op.result)

    def op_binary(self, op, left, right):
        binop = defs.binary_opcodes[op.opcode]
        if op.type.is_int:
            genop = binop_int[binop][0 if op.type.signed else 1]
        else:
            genop = binop_float[binop]
        return genop(self.builder, left, right, op.result)

    def op_compare(self, op, left, right):
        cmpop = defs.compare_opcodes[op.opcode]
        type = op.args[0].type
        if (type.is_int and type.signed) or type.is_bool:
            cmp, op = self.builder.icmp, compare_signed_int[cmpop]
        elif type.is_int:
            cmp, op = self.builder.icmp, compare_unsiged_int[cmpop]
        else:
            cmp, op = self.builder.fcmp, compare_float[cmpop]

        return cmp(op, left, right, op.result)

    # __________________________________________________________________

    def op_call(self, op, function, args):
        return self.builder.call(function, args)

    def op_call_math(self, op, name, args):
        # Math is resolved by an LLVM postpass
        argtypes = [arg.type for arg in args]
        lfunc_type = self.llvm_type(Function(op.type, argtypes))
        lfunc = self.lmod.get_or_insert_function(
            lfunc_type, 'pykit.math.%s.%s' % (map(str, argtypes), name.lower()))
        return self.builder.call(lfunc, args, op.result)

    # __________________________________________________________________

    def op_getfield(self, op, struct, attr):
        index = const_i32(op.type.names.index(attr))
        return self.builder.extract_value(struct, index, op.result)

    def op_setfield(self, op, struct, attr, value):
        index = const_i32(op.type.names.index(attr))
        return self.builder.insert_element(struct, value, index, op.result)

    # __________________________________________________________________

    def op_getindex(self, op, array, indices):
        return self.builder.gep(array, indices, op.result)

    def op_setindex(self, op, array, indices, value):
        ptr = self.builder.gep(array, indices)
        self.builder.store(ptr, value)

    # __________________________________________________________________

    def op_getindex(self, op, array, indices):
        return self.builder.gep(array, indices, op.result)

    # __________________________________________________________________

    def op_alloca(self, op):
        return self.builder.alloca(self.llvm_type(op.type), op.result)

    def op_load(self, op, stackvar):
        return self.builder.load(stackvar, op.result)

    def op_store(self, op, stackvar, value):
        self.builder.store(value, stackvar, op.result)

    # __________________________________________________________________

    def op_jump(self, op, block):
        self.builder.branch(block, op.result)

    def op_cbranch(self, op, test, true_block, false_block):
        self.builder.cbranch(test, true_block, false_block, op.result)

    def op_phi(self, op, *args):
        phi = self.builder.phi(self.llvm_type(op.type), op.result)
        self.phis.append(op)
        return phi

    def op_ret(self, op, value):
        if value is None:
            assert self.func.type.restype.is_void
            self.builder.ret_void()
        else:
            self.builder.ret(value)

    def op_phi(self, op, *args):
        return self.builder.phi(self.llvm_type(op.type), op.result)

    # __________________________________________________________________

    def op_sizeof(self, op, type):
        int_type = self.llvm_type(op.type)
        item_type = self.llvm_type(type)
        return sizeof(self.builder, item_type, int_type, op.result)

    def op_addressof(self, op, func):
        assert func.address
        addr = const_int(i64, func.address)
        return self.builder.inttoptr(addr, self.llvm_type(Pointer(func.type)))

    # __________________________________________________________________

    def op_ptradd(self, op, ptr, val):
        return self.builder.gep(ptr, [val], op.result)

    def op_ptrload(self, op, ptr):
        return self.builder.load(ptr, op.result)

    def op_ptrstore(self, op, ptr, val):
        return self.builder.store(val, ptr, op.result)

    def op_ptrcast(self, op, val):
        return self.builder.bitcast(val, self.llvm_type(op.type), op.result)

    def op_ptr_isnull(self, op, val):
        intval = self.builder.ptrtoint(val, self.llvm_type(Int64))
        return self.builder.icmp(lc.ICMP_EQ, intval, zero(intval.type), op.result)

    # __________________________________________________________________


def allocate_blocks(llvm_func, pykit_func):
    """Return a dict mapping pykit blocks to llvm blocks"""
    blocks = {}
    for block in pykit_func.blocks:
        blocks[block] = llvm_func.append_basic_block(pykit_func.name)

    return blocks

def update_phis(phis, blockmap, valuemap):
    """
    Update LLVM phi values given a list of pykit phi values and block and
    value dicts mapping pykit values to LLVM values
    """
    for phi in phis:
        llvm_phi = valuemap[phi]
        for block, value in zip(phi.args[0], phi.args[1]):
            llvm_phi.add_incoming(valuemap[value], blockmap[block])

#===------------------------------------------------------------------===
# Pass to group operations such as add/mul
#===------------------------------------------------------------------===

class LLVMArgLoader(ArgLoader):
    """
    Load Operation arguments as LLVM values passed and extra *args to the
    Translator.
    """

    def __init__(self, engine, llvm_module, lfunc, blockmap):
        self.engine = engine
        self.llvm_module = llvm_module
        self.lfunc = lfunc
        self.blockmap = blockmap

    def load_GlobalValue(self, arg, valuemap):
        if arg.external:
            value = self.lmod.get_or_insert_function(llvm_type(arg.type))
            if arg.address:
                self.engine.add_global_mapping(value, arg.address)
        else:
            assert arg.value
            value = arg.value.const

        return value

    def load_Block(self, arg, valuemap):
        return self.blockmap[arg]


def translate(func, engine, llvm_module):
    verify_lowlevel(func)

    ### Create lfunc ###
    lfunc = llvm_module.add_function(llvm_type(func.type), func.name)
    blockmap = allocate_blocks(lfunc, func)

    ### Create visitor ###
    translator = Translator(func, lfunc, llvm_type, llvm_module)
    visitor = opgrouper(translator)

    ### Codegen ###
    argloader = LLVMArgLoader(engine, llvm_module, lfunc, blockmap)
    valuemap = vvisit(visitor, func, argloader)
    update_phis(translator.phis, blockmap, valuemap)

    return lfunc

def run(func, env):
    return translate(func, env["codegen.llvm.engine"], env["codegen.llvm.module"])