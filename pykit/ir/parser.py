# -*- coding: utf-8 -*-

"""
Parse pykit IR.
"""

from __future__ import print_function, division, absolute_import
import operator
from collections import namedtuple
import pgen2.parser, pgen2.pgen

# ______________________________________________________________________

Module  = namedtuple("Module", ["globals", "functions"])
Function = namedtuple("Function", ["name", "restype", "argtypes",
                                   "argnames", "blocks"])
Global  = namedtuple("Global",  ["name", "type"])
Block   = namedtuple("Block",   ["label", "stats"])
Stat    = namedtuple("Stat",    ["dest", "opname", "type", "args"])
Type    = namedtuple("Type",    ["name"])
Pointer = namedtuple("Pointer", ["base"])
Struct  = namedtuple("Struct",  ["types"])

# ______________________________________________________________________

def b_global(args):
    return Global(args[1], args[3])

def b_function(args):
    restype, name, _, func_args, _, _ = args[1]
    blocks = args[2:-2] # omit the footer and newline
    argtypes, argnames = func_args[::2], func_args[1::2]
    return Function(name, restype, argtypes, argnames, blocks)

def b_block(args):
    return Block(args[0], args[2:])

def b_type(args):
    ty, tail = Type(args[0]), args[1:]
    for i in range(len(tail)):
        ty = Pointer(ty)
    return ty

def b_op(args):
    _, dest, _, _, type, _, opname, _, argnames, _ = args
    return Stat(dest, opname, type, argnames)

id_ = lambda x: x

rules = {
    'global': b_global,
    'function': b_function,
    'block': b_block,
    'op': b_op,
    'type': b_type,

    'varname': operator.itemgetter(1),
    'id': operator.itemgetter(0),
}

# ______________________________________________________________________

def build_ast(parse_result, symmap):
    """Built an AST from a parse tree and a symbol map"""
    (sym, tok, _), args = parse_result
    type = symmap[sym]
    visit_fn = rules.get(type, lambda x: x)

    result = []
    for ((newsym, newtok, n), newargs) in args:
        if newtok not in ('NEWLINE', 'ENDMARKER'):
            if newsym in symmap:
                result.append(build_ast(((newsym, newtok, n), newargs), symmap))
            else:
                result.append(newtok)

    return visit_fn(result)

# ______________________________________________________________________

ty = "NAME '*'*"

grammar = """
decls    : (function | global)* ENDMARKER
function : 'function' header block* footer NEWLINE
header   : type NAME '(' arg * ')' '{'

arg      : type varname
id       : ( NAME | NUMBER )
varname  : '%' id
type     : NAME '*'*

block    : NAME ':' op+
op       : '%' id '=' '(' type ')' NAME '(' varname * ')'
global   : 'global' varname '=' type NEWLINE

footer   : '}'
"""

def make_parser(grammar):
    grammar_st0 = pgen2.parser.parse_string(grammar)
    return pgen2.pgen.buildParser(grammar_st0)

grammar_parser  = make_parser(grammar)
type_parser     = make_parser("p : type\ntype : {type} ENDMARKER\n".format(type=ty))

def parse(source, parser=grammar_parser):
    "Return a list of parsed statements (Function|Block|Stat)"
    result = parser.parseString(source)
    symmap = parser.symbolToStringMap()
    return result, symmap

# ______________________________________________________________________

def build(parse_result):
    parsed, symmap = parse_result
    _, decls = parsed
    return [build_ast(decl, symmap) for decl in decls if decl[0][0] in symmap]

# ______________________________________________________________________

def from_assembly(source, parser=grammar_parser):
    return build(parse(source, parser))