# -*- coding: utf-8 -*-

"""
Parse numba IR.
"""

from __future__ import print_function, division, absolute_import

from collections import namedtuple
from lepl import *

# ______________________________________________________________________

Module = namedtuple("Module", ["externals", "functions"])
Function = namedtuple("Function", ["name", "args", "blocks"])
External = namedtuple("External", ["name", "restype", "args"])
Block = namedtuple("Block", ["label", "stats"])
Stat = namedtuple("Stat", ["dest", "opname", "type", "args"])

# ______________________________________________________________________

def lit(name):
    return Drop(Literal(name))

par = lambda value: lit("(") & value & lit(")")

ws = ~Whitespace()[:]
nl = ~Newline()
ident = Regexp("[a-zA-Z0-9_]+")
value = lit("%") & ident

# ______________________________________________________________________

def p_header(args):
    name, arglist = args[0], args[1:]
    args = list(map(tuple, arglist)) # [(argname, argtype)]
    return Function(name, args, [])

def p_block(args):
    label, = args
    return Block(label, [])

def p_stat(args):
    dest, type, opname, arglist = args
    return Stat(dest, opname, type, list(map(tuple, arglist)))

# ______________________________________________________________________

repeat = lambda x: Star(x|ws & nl) & ws

def parse(source):
    "Return a list of parsed statements (Function|Block|Stat)"
    # TODO: Parse grammar as a string and then use lepl
    with Separator(ws):
        type = ident
        arg = type & value >List
        args = Optional(arg) & Star(lit(",") & arg)
        arglist = par(args)
        header = lit("function") & ident & arglist >p_header
        statargs = arglist >List
        stat = ws & value & lit("=") & par(type) & ident & statargs & nl >p_stat
        block = ws & ident & lit(":") >p_block
        stats = repeat(block|stat)
        function = header & lit("{") & nl & block & nl & stats & lit("}") & ws
        functions = repeat(function)

    # stats.parse(source)
    return functions.parse(source)

# ______________________________________________________________________

def build(parse_result):
    functions = []
    function, stats = parse_result[0], parse_result[1:]

    # Populate Functions and Blocks
    for stat in parse_result:
        if isinstance(stat, Function):
            function = stat
            functions.append(function)
        elif isinstance(stat, Block):
            block = stat
            function.blocks.append(block)
        else:
            block.stats.append(stat)

    return functions

# ______________________________________________________________________

def from_assembly(source):
    return build(parse(source))