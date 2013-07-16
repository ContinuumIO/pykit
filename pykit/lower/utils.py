# -*- coding: utf-8 -*-

"""
Lowering utilities.
"""

from __future__ import print_function, division, absolute_import
from pykit import types
from pykit.ir import Builder, GlobalValue

def _verify_args(builder, op):
    for arg in op.args:
        if isinstance(arg, list):
            raise NotImplementedError("External call with list in arguments")

class RuntimeLowering(object):
    """
    Lower assembly Operations into runtime calls, e.g.
        Op("thread_start") -> Op("call", "thread_start", [])
    """

    def __init__(self, func):
        self.mod = func.module
        self.builder = Builder(func)
        self.func = func

    def lower_ops_into_runtime(self, names, insert_decl=False):
        """Lower all ops listed in `names` into runtime calls"""
        names = set(names)
        for op in self.func.ops:
            if op.opcode in names:
                self.lower_into_runtime(op, insert_decl)

    def lower_into_runtime(self, op, insert_decl=False):
        """
        Lower op into a runtime call.

        :param decl: Whether to insert an external declaration if not present
        """
        _verify_args(op)
        if insert_decl and not self.mod.get_global(op.opcode):
            signature = types.Function(op.type, [arg.type for arg in op.args])
            self.mod.add_global(GlobalValue(op.opcode, signature, external=True))

        call = self.builder.gen_call_external(op.opcode, op.args, op.result)
        op.replace(call)