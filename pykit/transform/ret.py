# -*- coding: utf-8 -*-

"""
Normalize returns so that the only return is in the exit block.
"""

from pykit import types
from pykit.ir import Builder, Undef

def run(func, env, return_block=None):
    """
    Rewrite 'ret' operations into jumps to a return block and assignments
    to a return variable.
    """
    b = Builder(func)
    return_block = return_block or func.add_block("pykit.return")

    # Allocate return variable
    if not func.type.restype.is_void:
        with b.at_front(func.startblock):
            return_var = b.alloca(types.Pointer(func.type.restype), [])
            b.store(Undef(func.type.restype), return_var)
    else:
        return_var = None

    # Repace 'ret' instructions with jumps and assignments
    for op in func.ops:
        if op.opcode == "ret":
            b.position_after(op)
            if return_var:
                b.store(return_var, op.args[0])
            b.jump(return_block)
            op.delete()

    with b.at_end(return_block):
        if return_var:
            result = b.load(return_var.type.base, [return_var])
        else:
            result = None

        b.ret(result)