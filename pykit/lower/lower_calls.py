# -*- coding: utf-8 -*-

"""
Lower calls.
"""

from pykit import types
from pykit.ir import visit, Const, FunctionPass

class Verify(object):
    """Verify the current state of calls"""

    def op_call(self, op):
        assert not op.args[0].type.is_object, "Object calls must have been resolved"

class ExceptionChecking(FunctionPass):
    """
    Insert exception checking for calls.

    Call metadata:

        exc.badval: check against bad value to propagate errors
        exc.raise:  raise error if bad value encountered
    """

    def op_call(self, op):
        self.builder.position_after(op)

        exc_badval = op.metadata.get("exc.badval")
        exc = op.metadata.get("exc.raise")

        if exc:
            self._handle_raise(op, exc_badval, exc)
        elif exc_badval is not None:
            self.builder.check_error(op, exc_badval)

    def _handle_raise(self, op, badval, exc):
        "Raise an exception if retval == badval"
        assert badval is not None
        cond = self.builder.eq(types.Bool, [op, badval])
        with self.builder.if_(cond):
            msg = op.metadata.get("exc.msg")
            args = [Const(msg)] if msg is not None else []
            exc = self.builder.new_exc(types.Exception, [exc] + args)
            self.builder.exc_throw(exc)

# call virtual

# call math

def run(func, env):
    """Generate runtime calls into thread library"""
    if env.get("verify"):
        visit(Verify(), func)
    visit(ExceptionChecking(func), func)