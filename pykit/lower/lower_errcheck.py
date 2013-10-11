# -*- coding: utf-8 -*-

"""
Lower exception-related instructions.
"""

from pykit import types
from pykit.ir import visit, FunctionPass

class LowerExceptionChecksCostful(FunctionPass):
    """
    Lower exception checks (check_error) using C-like checks:

        if (result == bad)
            goto error;
    """

    def op_check_error(self, op):
        result, badval = op.args
        self.builder.position_after(op)

        with self.builder.if_(self.builder.eq(types.Bool, [result, badval])):
            self.builder.gen_error_propagation()

        op.delete()

def lower_costful(func, env=None):
    visit(LowerExceptionChecksCostful(func), func)

run = lower_costful