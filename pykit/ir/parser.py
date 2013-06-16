# -*- coding: utf-8 -*-

"""
Parse pykit IR.
"""

from __future__ import print_function, division, absolute_import

from collections import namedtuple
import pgen2.parser, pgen2.pgen

# ______________________________________________________________________

Module = namedtuple("Module", ["globals", "functions"])
Function = namedtuple("Function", ["name", "args", "blocks"])
Global = namedtuple("Global", ["name", "type"])
Block = namedtuple("Block", ["label", "stats"])
Stat = namedtuple("Stat", ["dest", "opname", "type", "args"])

# ______________________________________________________________________

def b_global(args):
    varname, type = args
    return Global(varname, type)

def b_function(args):
    header, blocks, footer = args
    name, args = header
    return Function(name, args, blocks)

def b_varname(args):
    return args[1]

def b_type(args):
    return args[0]

def b_block(args):
    label, ops = args
    return Block(label, ops)

def b_stat(args):
    dest, type, opname, argnames = args
    return Stat(dest, opname, type, argnames)

id_ = lambda x: x

rules = {
    'global': b_global,
    'function': b_function,
    'block': b_block,
    'stat': b_stat,
    'varname': b_varname,
    'type': b_type,
}

# ______________________________________________________________________

def build_ast(parse_result, symmap):
    (sym, tok, _), args = parse_result
    type = symmap[sym]
    visit_fn = rules.get(type, lambda x: x)

    result = []
    for ((newsym, newtok, n), newargs) in args:
        if newsym in symmap:
            result.append(build_ast(((newsym, newtok, n), newargs), symmap))
        else:
            result.append(newtok)

    return visit_fn(result)

# ______________________________________________________________________

grammar = """
decls    : (function | global)* ENDMARKER
function : 'function' header (block op*)* footer NEWLINE
header   : type NAME '(' arg * ')' '{'

arg      : type varname
id       : ( NAME | NUMBER )
varname  : '%' id
type     : NAME

block    : NAME ':'
op       : '%' id '=' '(' type ')' NAME '(' varname * ')'
global   : 'global' varname '=' type NEWLINE

footer   : '}'
"""

grammar_st0 = pgen2.parser.parse_string(grammar)
grammar_parser = pgen2.pgen.buildParser(grammar_st0)

def parse(source):
    "Return a list of parsed statements (Function|Block|Stat)"
    result = grammar_parser.parseString(source)
    symmap = grammar_parser.symbolToStringMap()
    # (sym, tok, _), args = result
    # print(symmap[sym], tok)
    # print(symmap)
    # print(args[-1])
    # print([symmap[arg[0][0]] for arg in args[:-1]])
    # stats.parse(source)
    # return functions.parse(source)
    return result, symmap

result = parse("""
global %foo = double

function double func(int %foo) {
entry:
    %f = (double) foo(%foo)
block:
    %g = (double) scotch(%foo)

}
""")

# ______________________________________________________________________

def build(parse_result):
    parsed, symmap = parse_result
    _, decls = parsed
    return [build_ast(decl, symmap) for decl in decls]

# ______________________________________________________________________

def from_assembly(source):
    return build(parse(source))

build(result)
# parse("%0 = (double) scotch(%foo)")

