# -*- coding: utf-8 -*-

"""
Function inlining.
"""

from pykit.error import CompileError
from pykit.analysis import loop_detection
from pykit.ir import Function, Builder, findallops, copy_function, verify
from pykit.transform import ret as ret_normalization

def rewrite_return(func):
    """Rewrite ret ops to assign to a variable instead, which is returned"""
    ret_normalization.run(func)
    [ret] = findallops(func, 'ret')
    [value] = ret.args
    ret.delete()
    return value

def inline(func, call):
    """
    Inline the call instruction into func.

    :param uses: defuse information
    """
    callee = call.args[0]
    # assert_inlinable(func, call, callee, uses)

    builder = Builder(func)
    builder.position_before(call)
    inline_header, inline_exit = builder.splitblock()
    new_callee = copy_function(callee, temper=func.temp)
    result = rewrite_return(new_callee)

    # Fix up arguments
    for funcarg, arg in zip(new_callee.args, call.args[1]):
        funcarg.replace_uses(arg)

    # Copy blocks
    after = inline_header
    for block in new_callee.blocks:
        block.parent = None
        func.add_block(block, after=after)
        after = block

    # Fix up wiring
    builder.jump(new_callee.startblock)
    with builder.at_end(new_callee.exitblock):
        builder.jump(inline_exit)

    # Fix up final result of call
    if result is not None:
        # non-void return
        result.unlink()
        result.result = call.result
        call.replace(result)
    else:
        call.delete()

    func.reset_uses()
    verify(func)

def assert_inlinable(func, call, callee, uses):
    """
    Verify that a function call can be inlined.

    We can inline generators if they are consumed in a single loop:

        - iter(g) must be in a loop header
        - next(g) must be in the loop body

    :return: None if inlineable, or an exception with a message
    """
    if not isinstance(callee, Function):
        return CompileError("Cannot inline external function: %s" % (callee,))

    yields = findallops(callee, 'yield')
    if yields:
        for use in uses[call]:
            if use.opcode not in ('iter', 'next'):
                return CompileError(
                    "Cannot inline generator with use %s" % (use,))

        if len(uses[call]) != 2:
            return CompileError("Can only")
        loops = loop_detection.find_natural_loops(func)
