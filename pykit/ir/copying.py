# -*- coding: utf-8 -*-

"""
Copy pykit IR.
"""

from __future__ import print_function, division, absolute_import
from functools import partial
from pykit.ir import (Module, Value, Function, Block, Constant, Op,
                      GlobalValue, Undef, FuncArg)
from pykit.utils import nestedmap, make_temper

def _lookup(module, function, valuemap, arg):
    """Helper to reconstruct Operations"""
    if isinstance(arg, (Block, Op)):
        result = valuemap[arg]
    elif isinstance(arg, FuncArg):
        result = function.get_arg(arg.result)
    elif isinstance(arg, Function) and module is not None:
        result = module.get_function(arg.name)
    elif isinstance(arg, GlobalValue) and module is not None:
        result = module.get_global(arg.name)
    else:
        result = arg # immutable

    return result

# ______________________________________________________________________

def copy_module(module, temper=None):
    raise NotImplementedError("not finished, needs to insert all functions"
                              "in valuemap first")

    new_module = Module(temper=temper)
    valuemap = {}

    ### Copy Globals
    for name, gv in module.globals.iteritems():
        name = new_module.temp(name)
        new_global = GlobalValue(name, gv.type, gv.external, gv.address, gv.value)
        new_module.add_global(new_global)

        valuemap[gv] = new_global

    ### Copy Functions
    for name, func in module.functions.iteritems():
        new_func = copy_function(func, module=new_module)
        new_func.name = new_module.temp(name)
        new_module.add_function(new_func)

        valuemap[func] = new_func

    return new_module

def copy_function(func, temper=None, module=None):
    """Copy a Function. `temper` may be given to"""
    temper = temper or make_temper()
    f = Function(func.name, list(func.argnames), func.type, temper=temper)
    valuemap = {}
    lookup = partial(_lookup, module or func.module, f, valuemap)

    ### Construct new Blocks
    for block in func.blocks:
        new_block = Block(temper(block.name), f)
        valuemap[block] = new_block
        f.add_block(new_block)

    ### Construct new Operations
    for block in func.blocks:
        new_block = valuemap[block]
        for op in block.ops:
            if op.opcode == 'phi':
                # Phi nodes may be circular, or may simply precede some of
                # their arguments
                args = []
            else:
                args = nestedmap(lookup, op.args)

            new_op = Op(op.opcode, op.type, args,
                        result=temper(op.result), parent=new_block)

            new_op.add_metadata(op.metadata)
            # assert new_op.result != op.result

            valuemap[op] = new_op
            new_block.append(new_op)

    for old_op in func.ops:
        if old_op.opcode == 'phi':
            new_op = valuemap[old_op]
            new_op.set_args(nestedmap(lookup, old_op.args))

    return f