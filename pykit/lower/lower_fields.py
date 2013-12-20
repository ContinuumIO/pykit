# -*- coding: utf-8 -*-

"""
Rewrite field accesses on pointers.
"""

from pykit.ir import Builder

def lower_fields(func, env=None):
    b = Builder(func)

    for op in func.ops:
        if op.opcode in ("getfield", "setfield") and op.args[0].type.is_pointer:
            b.position_before(op)
            p = op.args[0]
            load = b.load(p.type.base, [p])
            args = [load] + op.args[1:]
            op.set_args(args)

            if op.opcode == "setfield":
                b.position_after(op)
                b.store(op, p)

run = lower_fields