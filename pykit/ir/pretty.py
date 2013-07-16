# -*- coding: utf-8 -*-

"""
Pretty print pykit IR.
"""

from __future__ import print_function, division, absolute_import
from pykit.utils import hashable

prefix = lambda s: '%' + s
indent = lambda s: '\n'.join('    ' + s for s in s.splitlines())
ejoin  = "".join
sjoin  = " ".join
ajoin  = ", ".join
njoin  = "\n".join
parens = lambda s: '(' + s + ')'

compose = lambda f, g: lambda x: f(g(x))

def pretty(value):
    formatter = formatters[type(value).__name__]
    return formatter(value)

def fmod(mod):
    gs, fs = mod.globals.values(), mod.functions.values()
    return njoin([njoin(map(pretty, gs)), "", njoin(map(pretty, fs))])

def ffunc(f):
    restype = ftype(f.type.restype)
    types, names = map(ftype, f.type.argtypes), map(prefix, f.argnames)
    args = ajoin(map(sjoin, zip(types, names)))
    header = sjoin(["function", restype, f.name + parens(args)])
    return njoin([header + " {", njoin(map(fblock, f.blocks)), "}"])

def farg(func_arg):
    return "%" + func_arg.result

def fblock(block):
    body = njoin(map(compose(indent, fop), block))
    return njoin([block.name + ':', body, ''])

def fop(op):
    return '%{0} = ({1}) {2}({3})'.format(op.result, ftype(op.type), op.opcode,
                                          ajoin(map(prefix, map(str, op.operands))))

def fconst(c):
    return 'const(%s, %s)' % (ftype(c.type), c.const)

def fglobal(val):
    return "global %{0} = {1}".format(val.name, ftype(val.type))

def fundef(val):
    return 'Undef'

def ftype(val):
    from pykit import types
    if hashable(val) and val in types.type2name:
        return types.type2name[val]
    return str(val)


formatters = {
    'Module':      fmod,
    'GlobalValue': fglobal,
    'Function':    ffunc,
    'FuncArg':     farg,
    'Block':       fblock,
    'Operation':   fop,
    'Constant':    fconst,
    'Undef':       fundef,
}