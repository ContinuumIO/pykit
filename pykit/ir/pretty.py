# -*- coding: utf-8 -*-

"""
Pretty print pykit IR.
"""

from __future__ import print_function, division, absolute_import
import io
from pykit.core.value import Module, Function, Operation

def pretty_format(value, out=None):
    if out is None:
        out = io.StringIO()
    formatter = formatters[type(value)]
    formatter(value, out)
    return out.getvalue()

def pretty_module(mod, out):
    for gv in mod.globals.values():
        out.write(u"global %%%s = %s\n" % (gv.name, gv.type))
    out.write(u"\n")
    for f in mod.functions.values():
        pretty_format(f, out)

def pretty_function(f, out):
    args = u", ".join(u"%s %s" % t for t in f.args)
    out.write(u"function %s %s(%s) {\n" % (f.name, f.type.return_type, args))
    for block in f.blocks:
        out.write(u"%s:\n" % block.name)
        for op in block.instrs:
            pretty_format(op, out)
        out.write(u"\n")
    out.write(u"}\n")

def pretty_operation(op, out):
    out.write(u"    %%%s = (%s) %s(%s)" % (op.result, op.type, op.opcode,
                                           u", ".join(op.args)))

formatters = {
    Module: pretty_module,
    Function: pretty_function,
    Operation: pretty_operation,
}