# -*- coding: utf-8 -*-

"""
Map the result IR to abstract LLVM.
"""

from __future__ import print_function, division, absolute_import

from llvmpy.api import llvm

from pykit.llvm import llvm_passes, llvm_types, llvm_utils, llvm_const
from pykit.llvm import llvm_context


# ______________________________________________________________________
# LLVM stuff

llvm_value_t = llvm.StructType.create(llvm_context, "unknown")
unknown_ptr = llvm.PointerType.getUnqual(llvm_value_t)

class LLVMBuilder(object):

    def __init__(self, name, opague_type, argnames):
        self.name = name
        self.opague_type = opague_type
        self.lmod = self.make_module(name)
        self.lfunc = self.make_func(self.lmod, name, opague_type, argnames)
        self.builder = self.make_builder(self.lfunc)

    # __________________________________________________________________

    @classmethod
    def make_module(cls, name):
        mod = llvm.Module.new('module.%s' % name, llvm_context)
        return mod

    @classmethod
    def make_func(cls, lmod, name, opague_type, argnames):
        argtys = [opague_type] * len(argnames)
        restype = opague_type
        lfunc = llvm_utils.get_or_insert_func(
            lmod, name, restype, argtys)
        return lfunc

    @classmethod
    def make_builder(cls, lfunc):
        # entry = cls.make_block(lfunc, "entry")
        builder = llvm.IRBuilder.new(llvm_context)
        # builder.SetInsertPoint(entry)
        return builder

    @classmethod
    def make_block(cls, lfunc, blockname):
        blockname = 'block_%s' % blockname
        return llvm_utils.make_basic_block(lfunc, blockname)

    # __________________________________________________________________

    def delete(self):
        self.lmod = None
        self.lfunc = None
        self.builder = None

    def verify(self):
        llvm_utils.verify_module(self.lmod)

    def add_block(self, blockname):
        return self.make_block(self.lfunc, blockname)

    def set_block(self, dstblock):
        self.builder.SetInsertPoint(dstblock)

    def run_passes(self, passes):
        llvm_passes.run_function_passses(self.lfunc, passes)

    def call_abstract(self, name, restype, *args):
        argtys = [x.getType() for x in args]
        callee = llvm_utils.get_or_insert_func(self.lmod, name,
                                               restype, argtys)
        callee.setLinkage(llvm.GlobalValue.LinkageTypes.ExternalLinkage)
        return self.builder.CreateCall(callee, args)

    def call_abstract_pred(self, name, *args):
        argtys = [x.getType() for x in args]
        retty = llvm_types.i1
        callee = llvm_utils.get_or_insert_func(self.lmod, name,
                                               retty, argtys)
        return self.builder.CreateCall(callee, args)


class LLVMOperationTyper(object):

    def __init__(self, builder):
        self.builder = builder

    def llvm_restype(self, operation):
        return self.builder.opague_type


class LLVMMapper(object):

    LLVMBuilder = LLVMBuilder

    def __init__(self, funcgraph, opctx):
        self.funcgraph = funcgraph
        self.opctx = opctx
        self.builder = self.LLVMBuilder(funcgraph.name,
                                        llvm_types.unknown_ptr, [])

        # Operation -> LLVM Value
        self.llvm_values = {}

        # Block -> llvm block
        self.llvm_blocks = {}

    def llvm_operation(self, operation, llvm_args):
        name = self.opctx.opname(operation.opcode)
        # include operation arity in name
        name = '%s_%d' % (name, len(operation.args))
        if self.opctx.is_boolean_operation(operation):
            restype = llvm_types.i1
        else:
            restype = self.builder.opague_type
        return self.builder.call_abstract(name, restype, *llvm_args)

    def process_op(self, var):
        # TODO: map this properly
        args = [self.llvm_values[arg]
                for arg in var.operation.args if arg.is_var]
        value = self.llvm_operation(var.operation, args)
        self.llvm_values[var] = value

    def make_llvm_graph(self):
        "Populate the LLVM Function with abstract IR"
        blocks = self.funcgraph.blocks
        assert blocks

        # Allocate blocks
        for block in blocks:
            self.llvm_blocks[block] = self.builder.add_block(block.label)

        # Generete abstract IR
        for block in blocks:
            # print("block", block.label, len(block.children))
            self.builder.builder.SetInsertPoint(self.llvm_blocks[block])

            for var in block.instrs[:-1]:
                self.process_op(var)

            if len(block.children) == 1:
                if block.instrs: self.process_op(block.instrs[-1])
                succ, = block.children
                self.builder.builder.CreateBr(self.llvm_blocks[succ])
            elif block.instrs:
                self.terminate_block(block)

        if not block.instrs or not self.opctx.is_return(blocks[-1]):
            # Terminate with return
            #self.builder.builder.CreateRetVoid()
            self.builder.builder.CreateRet(
                llvm_const.null(self.builder.opague_type))

        print(self.builder.lfunc)
        self.builder.verify()
        return self.builder.lfunc

    def terminate_block(self, block):
        "Terminate a block with conditional branch"
        op = block.instrs[-1].operation

        assert self.opctx.is_terminator(op), op
        assert self.opctx.is_conditional_branch(op)
        assert len(block.children) == 2

        cond = self.opctx.get_condition(op)
        lcond = self.llvm_values[cond]

        succ1, succ2 = block.children
        self.builder.builder.CreateCondBr(
            lcond, self.llvm_blocks[succ1], self.llvm_blocks[succ2])